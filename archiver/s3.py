import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
import hashlib
import logging
import os
import sys
import threading


class ProgressPercentage(object):

    '''Display upload progress with callback'''

    def __init__(self, filename):
        self._filename    = filename
        self._size        = int(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock        = threading.Lock()
    
    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            pct = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                f'\r -> {self._filename} {self._seen_so_far}/{self._size} ({pct:.2f}%)'
                )
            sys.stdout.flush()

    def __del__(self):
        sys.stdout.write('\n')


def multipart_upload(local_path, bucket, key_path, config, extra_args=None):

    '''Perform the upload, with S3 client handling multi-part actions'''

    s3 = boto3.resource('s3')
    progress_tracker = ProgressPercentage(local_path)
    s3.meta.client.upload_file(local_path, bucket, key_path,
                               ExtraArgs=extra_args,
                               Config=config,
                               Callback=progress_tracker
    )

    return s3.meta.client.head_object(Bucket=bucket, Key=key_path)


def calculate_etag(path, chunk_size):

    '''Calculate the md5 or AWS etag for files larger than chunk size (default is 5MB)'''

    md5s = []

    with open(path, 'rb') as handle:
        while True:
            data = handle.read(chunk_size)
            if not data:
                break
            md5s.append(hashlib.md5(data))

    if len(md5s) == 1:
        return f'{md5s[0].hexdigest()}'

    digests = b''.join(m.digest() for m in md5s)
    digests_md5 = hashlib.md5(digests)
    return f'{digests_md5.hexdigest()}-{len(md5s)}'
