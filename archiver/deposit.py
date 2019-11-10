from boto3.s3.transfer import TransferConfig
import json

from .asset import Asset
from .batch import Batch
from .s3 import calculate_etag
from .s3 import multipart_upload


def calculate_chunk_bytes(chunk_string):
    if chunk_string.endswith('MB'):
        return int(chunk_string[:-2]) * (1024**2)
    elif chunk_string.endswith('GB'):
        return int(chunk_string[:-2]) * (1024**3)
    else:
        raise ConfigException


def deposit(args):

    '''Deposit a set of files to AWS'''

    batch = Batch(args)
    chunk_bytes = calculate_chunk_bytes(args.chunk)
    print(f'Running deposit subcommand with these options:')
    print(f'  - Target Bucket: {args.bucket}')
    print(f'  - Storage Class: {args.storage}')
    print(f'  - Chunk Size:    {args.chunk} ({chunk_bytes} bytes)')
    print()
    
    config = TransferConfig(multipart_threshold=chunk_bytes, 
                            max_concurrency=10,
                            multipart_chunksize=chunk_bytes, 
                            use_threads=True
                            )

    print(f'Depositing {len(batch.contents)} assets ...')
    for n, asset in enumerate(batch.contents, 1):
        header = f'({n}) {asset.filename.upper()}'
        print('\n' + header)
        print('=' * len(header))
        print(f'    FILE: {asset.local_path}')
        asset.key_path = f'{batch.name}/{asset.filename}'
        print(f' KEYPATH: {asset.key_path}')
        print(f'     EXT: {asset.extension}')
        print(f'   MTIME: {asset.mtime}')
        print(f'   BYTES: {asset.bytes}')
        print(f'     MD5: {asset.md5}')
        expected_etag = calculate_etag(asset.local_path, chunk_size=chunk_bytes)
        print(f'    ETAG: {expected_etag}')
        print()
        
        extras = {'Metadata': {'md5': asset.md5,
                               'bytes': str(asset.bytes)},
                  'StorageClass': args.storage}

        # Send the file
        response = multipart_upload(asset.local_path, 
                                    args.bucket, 
                                    asset.key_path, 
                                    extra_args=extras,
                                    config=config)

        #resp_meta = json.loads(response)
        #print(resp_meta)
        s3md5 = response['ResponseMetadata']['HTTPHeaders']['x-amz-meta-md5']

        if s3md5 == asset.md5:
            print(f' -> {s3md5} = {asset.md5} -> MD5 match! Transfer success!')
        else:
            print(f' -> Something went wrong.')

        print()
