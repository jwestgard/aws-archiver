import boto3
from botocore.exceptions import ClientError
import hashlib
import logging
import os
import sys
import threading

from .asset import Asset
from .batch import Batch


class ProgressPercentage():

    '''Display upload progress with callback'''

    def __init__(self, asset):
        self.asset = asset
        self._seen_so_far = 0
        self._lock = threading.Lock()
    
    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            pct = (self._seen_so_far / self.asset.bytes) * 100
            sys.stdout.write(f'\r  {self.asset.filename} -> ' +    
                             f'{self._seen_so_far}/{self.asset.bytes} ({pct:.2f}%)'
                )
            sys.stdout.flush()


def calculate_etag(path, chunk_size):

    '''Calculate the AWS etag (md5 or hash tree for files larger than chunk size)'''

    md5s = []
    with open(path, 'rb') as handle:
        while True:
            data = handle.read(chunk_size)
            if not data:
                break
            md5s.append(hashlib.md5(data))

    if len(md5s) == 1:
        return md5s[0].hexdigest()
    else:
        digests = hashlib.md5(b''.join([m.digest() for m in md5s]))
        return f'{digests.hexdigest()}-{len(md5s)}'


def deposit(args):

    '''Deposit a set of files to AWS'''

    batch = Batch(args)

    # Deisplay batch configuration information to the user
    sys.stdout.write(f'Running deposit command with the following options:\n\n')
    sys.stdout.write(f'  - Target Bucket: {batch.bucket}\n')
    sys.stdout.write(f'  - Storage Class: {batch.storage_class}\n')
    sys.stdout.write(f'  - Chunk Size: {args.chunk} ({batch.chunk_bytes} bytes)\n')
    sys.stdout.write(f'  - Use Threads: {batch.use_threads}\n')
    sys.stdout.write(f'  - Max Threads: {batch.max_threads}\n\n')

    # Process and transfer each asset in the batch contents
    sys.stdout.write(f'Depositing {len(batch.contents)} assets ...\n')
    for n, asset in enumerate(batch.contents, 1):
        asset.header = f'({n}) {asset.filename.upper()}'
        asset.key_path = f'{batch.name}/{asset.filename}'
        asset.expected_etag = calculate_etag(asset.local_path, 
                                             chunk_size=batch.chunk_bytes)

        # Prepare custom metadata to attach to the asset
        asset.extra_args = {'Metadata': {
                                'md5': asset.md5,
                                'bytes': str(asset.bytes)
                                },
                            'StorageClass': batch.storage_class
        }

        # Display Asset information to the user
        sys.stdout.write(f'\n{asset.header}\n{"=" * len(asset.header)}\n')
        sys.stdout.write(f'    FILE: {asset.local_path}\n')
        sys.stdout.write(f' KEYPATH: {asset.key_path}\n')
        sys.stdout.write(f'     EXT: {asset.extension}\n')
        sys.stdout.write(f'   MTIME: {asset.mtime}\n')
        sys.stdout.write(f'   BYTES: {asset.bytes}\n')
        sys.stdout.write(f'     MD5: {asset.md5}\n')
        sys.stdout.write(f'    ETAG: {asset.expected_etag}\n\n')

        # Send the file, optionally in multipart, multithreaded mode
        s3 = boto3.resource('s3')
        progress_tracker = ProgressPercentage(asset)
        s3.meta.client.upload_file(asset.local_path, 
                                   batch.bucket, 
                                   asset.key_path, 
                                   ExtraArgs=asset.extra_args,
                                   Config=batch.aws_config,
                                   Callback=progress_tracker
        )

        # Validate the upload with a head request to get the remote Etag
        sys.stdout.write('\n\n  Upload complete! Verifying...\n')
        response = s3.meta.client.head_object(Bucket=batch.bucket, Key=asset.key_path)
        # Pull the AWS etag from the response and strip quotes
        remote_etag = response['ResponseMetadata']['HTTPHeaders']['etag'].replace('"','')
        sys.stdout.write(f'    -> Local:  {asset.expected_etag}\n')
        sys.stdout.write(f'    -> Remote: {remote_etag}\n\n')
        if remote_etag == asset.expected_etag:
            sys.stdout.write(f'  ETag match! Transfer success!\n')
        else:
            sys.stdout.write(f'  Something went wrong.\n')

