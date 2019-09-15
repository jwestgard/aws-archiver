import boto3

from .batch import Batch
from .asset import Asset

def deposit(args):
    batch = Batch(args.mapfile)
    
    for item in batch.contents:
        asset = Asset(item[1], item[0])
        print(asset.path, asset.md5)