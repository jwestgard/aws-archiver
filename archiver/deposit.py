import boto3
import hashlib
from .batch import Batch
from .asset import Asset


def deposit(args):

    '''Deposit a set of files to AWS'''

    batch = Batch(args)

    for n, asset in enumerate(batch.contents, 1):
        header = f'({n}) {asset.filename.upper()}'
        print('\n' + header)
        print('=' * len(header))
        print(f'  PATH: {asset.path}')
        print(f'   EXT: {asset.extension}')
        print(f' MTIME: {asset.mtime}')
        print(f' BYTES: {asset.bytes}')
        print(f'   MD5: {asset.md5}')

