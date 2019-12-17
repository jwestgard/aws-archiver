import csv
import json
import os
import sys
import threading
from datetime import datetime

from boto3.exceptions import S3UploadFailedError
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

from .asset import Asset
from .exceptions import ConfigException, PathOutOfScopeException


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


class Batch:
    """
    Class representing a set of resources to be archived,
    and an AWS configuration where they will be archived.
    """

    def __init__(
            self, name, bucket, root='.', log_dir=None,
            chunk_size=None, storage_class=None, max_threads=None,
            mapfile=None, asset=None
    ):
        """
        Set up a batch of assets to be loaded. Any assets whose local paths don't exist are omitted from the batch.
        """
        self.name = name
        self.chunk_bytes = calculate_chunk_bytes(chunk_size if chunk_size is not None else DEFAULT_CHUNK_SIZE)
        self.bucket = bucket
        self.root = os.path.abspath(root)
        if not self.root.endswith('/'):
            self.root += '/'
        self.storage_class = storage_class if storage_class is not None else DEFAULT_STORAGE_CLASS

        self.log_dir = log_dir if log_dir is not None else DEFAULT_LOG_DIR
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

        self.max_threads = int(max_threads if max_threads is not None else DEFAULT_MAX_THREADS)
        if self.max_threads == 1:
            self.use_threads = False
        else:
            self.use_threads = True

        self.contents = []
        self.stats = {
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
        if mapfile:
            self.mapfile = mapfile
            with open(mapfile) as handle:
                for line in handle:
                    # using None as delimiter splits on any whitespace
                    md5, path = line.strip().split(None, 1)
                    self.add_asset(path, md5)

        # Otherwise process a single asset path passed as an argument
        else:
            self.mapfile = None
            self.add_asset(asset)

        # Set up the AWS transfer configuration for the batch
        self.aws_config = TransferConfig(
            multipart_threshold=self.chunk_bytes,
            max_concurrency=self.max_threads,
            multipart_chunksize=self.chunk_bytes,
            use_threads=self.use_threads
        )

    def add_asset(self, path, md5=None):
        try:
            self.stats['total_assets'] += 1
            asset = Asset(path, self.root, md5)
            self.contents.append(asset)
            self.stats['assets_found'] += 1
        except FileNotFoundError as e:
            self.stats['assets_missing'] += 1
            print(f'Skipping {path}: {e}', file=sys.stderr)
        except PathOutOfScopeException as e:
            self.stats['assets_ignored'] += 1
            print(f'Skipping {path}: {e}', file=sys.stderr)

    def deposit(self, s3):
        begin = datetime.now()
        self.stats['deposit_begin'] = begin.isoformat()

        json_logfile_name = os.path.join(self.log_dir, self.name + '.json')

        if self.mapfile:
            mapfile_path = os.path.join(self.log_dir, self.mapfile + '.tmp')
            mapfile = open(mapfile_path, 'w+')
            fieldnames = ['id', 'relpath', 'filename', 'md5', 'bytes', 'keypath', 'etag', 'result']
            writer = csv.DictWriter(mapfile, fieldnames=fieldnames)
            writer.writeheader()
        else:
            mapfile = None
            writer = None

        # Process and transfer each asset in the batch contents
        sys.stdout.write(f'Depositing {len(self.contents)} assets ...\n')

        with open(json_logfile_name, 'w') as json_log:
            for n, asset in enumerate(self.contents, 1):
                header = f'({n}) {asset.filename.upper()}'
                key_path = f'{self.name}/{asset.relpath}'
                expected_etag = asset.calculate_etag(chunk_size=self.chunk_bytes)

                # Prepare custom metadata to attach to the asset
                asset.extra_args = {
                    'StorageClass': self.storage_class,
                    'Metadata': {
                        'md5': asset.md5,
                        'bytes': str(asset.bytes)
                    }
                }

                # Display Asset information to the user
                sys.stdout.write(f'\n{header}\n{"=" * len(header)}\n')
                sys.stdout.write(f'    FILE: {asset.local_path}\n')
                sys.stdout.write(f' KEYPATH: {key_path}\n')
                sys.stdout.write(f'     EXT: {asset.extension}\n')
                sys.stdout.write(f'   MTIME: {asset.mtime}\n')
                sys.stdout.write(f'   BYTES: {asset.bytes}\n')
                sys.stdout.write(f'     MD5: {asset.md5}\n')
                sys.stdout.write(f'    ETAG: {expected_etag}\n\n')

                # Send the file, optionally in multipart, multithreaded mode
                progress_tracker = ProgressPercentage(asset, self)
                self.stats['assets_transmitted'] += 1
                try:
                    s3.meta.client.upload_file(
                        asset.local_path,
                        self.bucket,
                        key_path,
                        ExtraArgs=asset.extra_args,
                        Config=self.aws_config,
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
                    response = s3.meta.client.head_object(Bucket=self.bucket, Key=key_path)
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
                    'relpath': asset.relpath,
                    'filename': asset.filename,
                    'md5': asset.md5,
                    'bytes': asset.bytes,
                    'keypath': key_path,
                    'etag': remote_etag,
                    'result': result
                }
                if writer is not None:
                    writer.writerow(row)

        if mapfile is not None:
            mapfile.close()

        end = datetime.now()
        self.stats['deposit_end'] = end.isoformat()
        self.stats['deposit_time'] = (end - begin).total_seconds()
