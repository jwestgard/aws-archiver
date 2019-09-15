import boto3

from .batch import Batch

def deposit(args):
    print(args)
    batch = Batch(mapfile)