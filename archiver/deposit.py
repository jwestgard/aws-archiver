import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
import logging
import os
import sys
import threading

from .batch import Batch
from .asset import Asset

BUCKET_NAME = "YOUR_BUCKET_NAME"


def deposit(args):

    '''Deposit a set of files to AWS'''

    batch = Batch(args)
    
    print(f'\nAWS Archiver -- Batch Deposit')
    print(f'Depositing {len(batch.contents)} assets ...')

    for n, asset in enumerate(batch.contents, 1):
        header = f'({n}) {asset.filename.upper()}'
        print('\n' + header)
        print('=' * len(header))
        print(f'  PATH: {asset.path}')
        print(f'   EXT: {asset.extension}')
        print(f' MTIME: {asset.mtime}')
        print(f' BYTES: {asset.bytes}')
        print(f'   MD5: {asset.md5}')


def multipart_upload(filepath):

    config = TransferConfig(multipart_threshold=1024 * 25, 
                            max_concurrency=10,
                            multipart_chunksize=1024 * 25, 
                            use_threads=True
                            )

    key_path = 'multipart_files/largefile.pdf'

    s3.meta.client.upload_file(file_path, BUCKET_NAME, key_path,
                               ExtraArgs={'ACL': 'public-read', 
                                          'ContentType': 'text/pdf'},
                               Config=config,
                               Callback=ProgressPercentage(file_path)
                               )


class ProgressPercentage(object):

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
    
    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()


def calculate_s3_etag(file_path, chunk_size=8 * 1024 * 1024):

    md5s = []

    with open(file_path, 'rb') as fp:
        while True:
            data = fp.read(chunk_size)
            if not data:
                break
            md5s.append(hashlib.md5(data))

    if len(md5s) == 1:
        return '"{}"'.format(md5s[0].hexdigest())

    digests = b''.join(m.digest() for m in md5s)
    digests_md5 = hashlib.md5(digests)
    return '"{}-{}"'.format(digests_md5.hexdigest(), len(md5s))
