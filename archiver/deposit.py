import boto3

from .batch import Batch
from .asset import Asset

def deposit(args):
    batch = Batch(args.mapfile)
    for n, item in enumerate(batch.contents, 1):
        asset = Asset(item[0], item[1])
        header = f'({n}) {asset.filename.upper()}'
        print('\n' + header)
        print('=' * len(header))
        print(f'  PATH: {asset.path}')
        print(f'   EXT: {asset.extension}')
        print(f' MTIME: {asset.mtime}')
        print(f' BYTES: {asset.bytes}')
        print(f'   MD5: {asset.md5}')
