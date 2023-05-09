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


def get_s3_client(profile_name, dry_run=False):
    """
    Set up a session with specified authentication profile.
    """
    if dry_run:
        from unittest.mock import MagicMock
        mock_s3_client = MagicMock()
        response = {'ResponseMetadata': {'HTTPHeaders': {'etag': 'DRY_RUN'}}}
        mock_s3_client.head_object = MagicMock(return_value=response)

        return mock_s3_client
    else:
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

    def __init__(self, manifest, bucket, asset_root, name=None, log_dir=None):
        """
        Set up a batch of assets to be loaded. Any assets whose local paths don't exist are omitted from the batch.
        """
        self.manifest = manifest
        self.overridden_name = name
        self.bucket = bucket

        if asset_root is None:
            self.asset_root = None
        else:
            self.asset_root = os.path.abspath(asset_root)
            if not self.asset_root.endswith('/'):
                self.asset_root += '/'

        self.log_dir = os.path.join(manifest.manifest_path, log_dir if log_dir is not None else DEFAULT_LOG_DIR)
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

        self.results_filename = os.path.join(self.log_dir, 'results.csv')
        self.manifest_filename = None
        self.contents = []

        self.stats = {
            'batch_name': self.overridden_name,
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

    def add_asset(self, path, batch_name=None, md5=None, relpath=None, manifest_row=None, etag=None):
        try:
            self.stats['total_assets'] += 1
            if (self.asset_root is not None) and (relpath is None):
                relpath = calculate_relative_path(self.asset_root, path)

            asset = Asset(path, batch_name=batch_name, md5=md5, relpath=relpath, manifest_row=manifest_row, etag=etag)
            self.contents.append(asset)
            self.stats['assets_found'] += 1
        except FileNotFoundError as e:
            self.stats['assets_missing'] += 1
            print(f'Skipping {path}: {e}', file=sys.stderr)
        except PathOutOfScopeException as e:
            self.stats['assets_ignored'] += 1
            print(f'Skipping {path}: {e}', file=sys.stderr)

    def deposit(self, profile_name, chunk_size=None, storage_class=None, max_threads=None, dry_run=False):
        s3_client = get_s3_client(profile_name, dry_run)

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
            f'  - AWS Profile: {profile_name}\n'
            f'  - Dry Run: {dry_run}\n\n'
        )

        begin = datetime.now()
        self.stats['deposit_begin'] = begin.isoformat()

        if self.manifest.manifest_filename:
            results_file_exists = os.path.exists(self.results_filename)
            results_file = open(self.results_filename, 'a')
            fieldnames = ['ID']
            # Include fields from the manifest in the results file
            if (len(self.contents) > 0):
                first_asset = self.contents[0]
                manifest_row = first_asset.manifest_row
                if manifest_row:
                    fieldnames.extend(manifest_row.keys())
            fieldnames.extend(['KEYPATH', 'ETAG', 'RESULT', 'STORAGEPROVIDER', 'STORAGELOCATION'])
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
                if self.overridden_name is not None:
                    print(f'using overridden name {self.overridden_name}')
                    key_path = f'{self.overridden_name}/{asset.relpath}'
                elif asset.batch_name is not None and asset.batch_name != '':
                    print(f'Using batch name from the row {asset.batch_name}')
                    key_path = f'{asset.batch_name}/{asset.relpath}'
                else:
                    print(f'Using the manifestpath {self.manifest.manifest_path}')
                    key_path = f'{self.manifest.manifest_path}/{asset.relpath}'

                # Check if ETAG exists
                if asset.etag is not None and asset.etag != '':
                    expected_etag = asset.etag
                else:
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

                if dry_run:
                    expected_etag = remote_etag

                if remote_etag == expected_etag:
                    self.stats['successful_deposits'] += 1
                    sys.stdout.write(f'  ETag match! Transfer success!\n')
                    result = 'success'
                else:
                    self.stats['failed_deposits'] += 1
                    sys.stdout.write(f'  Something went wrong.\n')
                    result = 'failed'

                row = {
                    'ID': n,
                    'KEYPATH': key_path,
                    'ETAG': remote_etag,
                    'RESULT': result,
                    'STORAGEPROVIDER': 'AWS',
                    'STORAGELOCATION': f'{self.bucket}/{key_path}'
                }
                if asset.manifest_row:
                    row.update(asset.manifest_row)

                if writer is not None:
                    writer.writerow(row)

        if results_file is not None:
            results_file.close()

        end = datetime.now()
        self.stats['deposit_end'] = end.isoformat()
        self.stats['deposit_time'] = (end - begin).total_seconds()
