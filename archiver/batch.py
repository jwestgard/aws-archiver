import csv
import json
import os
import sys
import threading
from datetime import datetime

import boto3
from boto3.exceptions import S3UploadFailedError
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError, ProfileNotFound

from enum import Enum, unique

from .asset import Asset
from .exceptions import ConfigException, PathOutOfScopeException, FailureException
from .utils import calculate_relative_path

def get_s3_client(profile_name):
    """
    Set up a session with specified authentication profile.
    """
    try:
        session = boto3.session.Session(profile_name=profile_name)
    except ProfileNotFound as e:
        print(e, file=sys.stderr)
        raise FailureException from e
    return session.resource('s3').meta.client


class ProgressPercentage:
    """Display upload progress using callbacks."""

    def __init__(self, asset, batch):
        self.asset = asset
        self.batch = batch
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            self.batch.stats['asset_bytes_transmitted'] += bytes_amount
            pct = (self._seen_so_far / self.asset.bytes) * 100
            sys.stdout.write(
                f'\r  {self.asset.filename} -> ' +
                f'{self._seen_so_far}/{self.asset.bytes} ({pct:.2f}%)'
            )
            sys.stdout.flush()


def calculate_chunk_bytes(chunk_string):
    """
    Return the chunk size in bytes after converting the human-readable chunk size specification.
    """
    if chunk_string.endswith('MB'):
        return int(chunk_string[:-2]) * (1024**2)
    elif chunk_string.endswith('GB'):
        return int(chunk_string[:-2]) * (1024**3)
    else:
        raise ConfigException("Chunk size must be given in MB or GB")


DEFAULT_CHUNK_SIZE = '4GB'
DEFAULT_STORAGE_CLASS = 'DEEP_ARCHIVE'
DEFAULT_MAX_THREADS = 10
DEFAULT_LOG_DIR = 'logs'
DEFAULT_MANIFEST_FILENAME = 'manifest.txt'


@unique
class ManifestFileType(Enum):
    """
    Enumeration of manifest file types
    """
    MD5_SUM = 1
    PATSY_DB = 2


class Batch:
    """
    Class representing a set of resources to be archived,
    and an AWS configuration where they will be archived.
    """

    def __init__(self, manifest_path, bucket, asset_root, name=None, log_dir=None):
        """
        Set up a batch of assets to be loaded. Any assets whose local paths don't exist are omitted from the batch.
        """
        self.manifest_path = manifest_path
        if name is not None:
            self.name = name
        else:
            self.name = os.path.basename(self.manifest_path)
        self.bucket = bucket

        if asset_root is None:
            self.asset_root = None
        else:
            self.asset_root = os.path.abspath(asset_root)
            if not self.asset_root.endswith('/'):
                self.asset_root += '/'

        self.log_dir = os.path.join(self.manifest_path, log_dir if log_dir is not None else DEFAULT_LOG_DIR)
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

        self.results_filename = os.path.join(self.log_dir, 'results.csv')
        self.manifest_filename = None
        self.contents = []

        self.stats = {
            'batch_name': self.name,
            'total_assets': 0,
            'assets_found': 0,
            'assets_missing': 0,
            'assets_ignored': 0,
            'assets_transmitted': 0,
            'asset_bytes_transmitted': 0,
            'successful_deposits': 0,
            'failed_deposits': 0,
            'deposit_begin': '',
            'deposit_end': '',
            'deposit_time': 0
        }

    # Read assets information from an md5sum-style listing
    def load_manifest(self, manifest):
        if os.path.isfile(self.results_filename):
            with open(self.results_filename, 'r') as results_file:
                results = csv.DictReader(results_file)
                completed = set((row.get('md5'), row.get('local_path')) for row in results)
        else:
            completed = set()

        self.manifest_filename = os.path.join(self.manifest_path, manifest)
        self.load_manifest_file(self.manifest_filename, completed)

    def load_manifest_file(self, manifest_filename, completed):
        """
        Adds all the assets in the given manifest_filename, skipping
        any entries that are in the "completed" set.

        :param manifest_filename: the filepath to the manifest file
        :param completed: the set of md5 and local_path entries that have been
                          already uploaded
        """
        # Determine type of manifest file
        manifest_file_type = Batch.manifest_file_type(manifest_filename)

        if manifest_file_type == ManifestFileType.MD5_SUM:
            self.load_md5sum_manifest_file(manifest_filename, completed)
        else:
            self.load_patsy_manifest_file(manifest_filename, completed)

    def load_md5sum_manifest_file(self, manifest_filename, completed):
        """
        Adds all the assets in the given manifest_filename, which is assumed to
        be in the "md5sum" format, skipping any entries that are in the
        "completed" set.

        :param manifest_filename: the filepath to the manifest file
        :param completed: the set of md5 and local_path entries that have been
                          already uploaded
        """
        with open(manifest_filename) as manifest_file:
            for line in manifest_file:
                if line is '':
                    continue
                else:
                    # using None as delimiter splits on any whitespace
                    md5, path = line.strip().split(None, 1)
                    if (md5, path) not in completed:
                        self.add_asset(path, md5)

    def load_patsy_manifest_file(self, manifest_filename, completed):
        """
        Adds all the assets in the given manifest_filename, which is assumed to
        be in the "patsy-db" format, skipping any entries that are in the
        "completed" set.

        :param manifest_filename: the filepath to the manifest file
        :param completed: the set of md5 and local_path entries that have been
                          already uploaded
        """
        with open(manifest_filename) as manifest_file:
            reader = csv.DictReader(manifest_file, delimiter=',')
            for row in reader:
                md5 = row['md5']
                path = row['filepath']
                relpath = row['relpath']
                if (md5, path) not in completed:
                    self.add_asset(path, md5, relpath=relpath)

    @staticmethod
    def manifest_file_type(manifest_filename):
        """
        Returns the ManifestFileType indicating which type of manifest
        the given file is.

        :param manifest_filename: the filepath to the manifest file
        :return: a ManifestFileType indicating the type of manifest
        """
        with open(manifest_filename) as manifest_file:
            # Read the first line
            line = manifest_file.readline().strip()

            if line == "md5,filepath,relpath":
                return ManifestFileType.PATSY_DB

        return ManifestFileType.MD5_SUM

    def add_asset(self, path, md5=None, relpath=None):
        try:
            self.stats['total_assets'] += 1
            if (self.asset_root is not None) and (relpath is None):
                relpath = calculate_relative_path(self.asset_root, path)

            asset = Asset(path, md5, relpath=relpath)
            self.contents.append(asset)
            self.stats['assets_found'] += 1
        except FileNotFoundError as e:
            self.stats['assets_missing'] += 1
            print(f'Skipping {path}: {e}', file=sys.stderr)
        except PathOutOfScopeException as e:
            self.stats['assets_ignored'] += 1
            print(f'Skipping {path}: {e}', file=sys.stderr)

    def deposit(self, profile_name, chunk_size=None, storage_class=None, max_threads=None):
        s3_client = get_s3_client(profile_name)

        if chunk_size is None:
            chunk_size = DEFAULT_CHUNK_SIZE
        chunk_bytes = calculate_chunk_bytes(chunk_size)
        storage_class = storage_class if storage_class is not None else DEFAULT_STORAGE_CLASS
        max_threads = int(max_threads if max_threads is not None else DEFAULT_MAX_THREADS)
        use_threads = (max_threads > 1)

        # Set up the AWS transfer configuration for the deposit
        aws_config = TransferConfig(
            multipart_threshold=chunk_bytes,
            max_concurrency=max_threads,
            multipart_chunksize=chunk_bytes,
            use_threads=use_threads
        )

        # Display batch configuration information to the user
        sys.stdout.write(
            f'Running deposit command with the following options:\n\n'
            f'  - Target Bucket: {self.bucket}\n'
            f'  - Local Asset Root: {self.asset_root}\n'
            f'  - Storage Class: {storage_class}\n'
            f'  - Chunk Size: {chunk_size} ({chunk_bytes} bytes)\n'
            f'  - Use Threads: {use_threads}\n'
            f'  - Max Threads: {max_threads}\n'
            f'  - AWS Profile: {profile_name}\n\n'
        )

        begin = datetime.now()
        self.stats['deposit_begin'] = begin.isoformat()

        if self.manifest_filename:
            results_file_exists = os.path.exists(self.results_filename)
            results_file = open(self.results_filename, 'a')
            fieldnames = ['id', 'filepath', 'filename', 'md5', 'bytes', 'keypath', 'etag', 'result', 'storagepath']
            writer = csv.DictWriter(results_file, fieldnames=fieldnames)
            if not results_file_exists:
                writer.writeheader()
        else:
            results_file = None
            writer = None

        # Process and transfer each asset in the batch contents
        sys.stdout.write(f'Depositing {len(self.contents)} assets ...\n')

        with open(os.path.join(self.log_dir, 'assets.json'), 'w') as json_log:
            for n, asset in enumerate(self.contents, 1):
                header = f'({n}) {asset.filename.upper()}'
                key_path = f'{self.name}/{asset.relpath}'
                expected_etag = asset.calculate_etag(chunk_size=chunk_bytes)

                # Prepare custom metadata to attach to the asset
                asset.extra_args = {
                    'StorageClass': storage_class,
                    'Metadata': {
                        'md5': asset.md5,
                        'bytes': str(asset.bytes)
                    }
                }

                # Display Asset information to the user
                sys.stdout.write(
                    f'\n{header}\n{"=" * len(header)}\n'
                    f'    FILE: {asset.local_path}\n'
                    f' KEYPATH: {key_path}\n'
                    f'     EXT: {asset.extension}\n'
                    f'   MTIME: {asset.mtime}\n'
                    f'   BYTES: {asset.bytes}\n'
                    f'     MD5: {asset.md5}\n'
                    f'    ETAG: {expected_etag}\n\n'
                )

                # Send the file, optionally in multipart, multithreaded mode
                progress_tracker = ProgressPercentage(asset, self)
                self.stats['assets_transmitted'] += 1
                try:
                    s3_client.upload_file(
                        asset.local_path,
                        self.bucket,
                        key_path,
                        ExtraArgs=asset.extra_args,
                        Config=aws_config,
                        Callback=progress_tracker
                    )
                except S3UploadFailedError as e:
                    self.stats['failed_deposits'] += 1
                    print(e, file=sys.stderr)
                    print('Continuing with the next asset', file=sys.stderr)
                    return

                # Validate the upload with a head request to get the remote Etag
                sys.stdout.write('\n\n  Upload complete! Verifying...\n')
                try:
                    response = s3_client.head_object(Bucket=self.bucket, Key=key_path)
                except ClientError as e:
                    self.stats['failed_deposits'] += 1
                    print(f'Error verifying {self.bucket}/{key_path}: {e}', file=sys.stderr)
                    print('Continuing with the next asset', file=sys.stderr)
                    return

                # Write response metadata to a line-oriented JSON file
                # See also: http://jsonlines.org/
                json.dump(
                    {'asset': f'{self.bucket}/{key_path}', 'response': response['ResponseMetadata']},
                    json_log
                )
                json_log.write('\n')

                # Pull the AWS etag from the response and strip quotes
                headers = response['ResponseMetadata']['HTTPHeaders']
                remote_etag = headers['etag'].replace('"', '')
                sys.stdout.write(f'    -> Local:  {expected_etag}\n')
                sys.stdout.write(f'    -> Remote: {remote_etag}\n\n')
                if remote_etag == expected_etag:
                    self.stats['successful_deposits'] += 1
                    sys.stdout.write(f'  ETag match! Transfer success!\n')
                    result = 'success'
                else:
                    self.stats['failed_deposits'] += 1
                    sys.stdout.write(f'  Something went wrong.\n')
                    result = 'failed'

                row = {
                    'id': n,
                    'filepath': asset.local_path,
                    'filename': asset.filename,
                    'md5': asset.md5,
                    'bytes': asset.bytes,
                    'keypath': key_path,
                    'etag': remote_etag,
                    'result': result,
                    'storagepath': f'{self.bucket}/{key_path}'
                }
                if writer is not None:
                    writer.writerow(row)

        if results_file is not None:
            results_file.close()

        end = datetime.now()
        self.stats['deposit_end'] = end.isoformat()
        self.stats['deposit_time'] = (end - begin).total_seconds()
