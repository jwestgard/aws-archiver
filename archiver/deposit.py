import boto3
import csv
import itertools
import sys

from botocore.exceptions import ProfileNotFound

from .batch import Batch, ConfigException


def get_s3_client(profile_name):
    """
    Set up a session with specified authentication profile.
    """
    try:
        session = boto3.session.Session(profile_name=profile_name)
    except ProfileNotFound as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    return session.resource('s3')


def deposit(args):
    """Deposit a set of files into AWS."""
    try:
        batch = Batch(
            name=args.name,
            bucket=args.bucket,
            root=args.root,
            chunk_size=args.chunk,
            storage_class=args.storage,
            max_threads=args.threads,
            log_dir=args.logs,
            mapfile=args.mapfile,
            asset=args.asset
        )
    except ConfigException as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    # Display batch configuration information to the user
    sys.stdout.write(f'Running deposit command with the following options:\n\n')
    sys.stdout.write(f'  - Target Bucket: {batch.bucket}\n')
    sys.stdout.write(f'  - Local Rootdir: {batch.root}\n')
    sys.stdout.write(f'  - Storage Class: {batch.storage_class}\n')
    sys.stdout.write(
        f'  - Chunk Size: {args.chunk} ({batch.chunk_bytes} bytes)\n'
        )
    sys.stdout.write(f'  - Use Threads: {batch.use_threads}\n')
    sys.stdout.write(f'  - Max Threads: {batch.max_threads}\n')
    sys.stdout.write(f'  - AWS Profile: {args.profile}\n\n')

    # Do the actual deposit to AWS
    batch.deposit(s3=get_s3_client(args.profile))


def batch_deposit(args):
    batches_file = args.batches_file
    fields = ('path', 'name', 'bucket', 'mapfile', 'root', 'logs', 'chunk', 'storage', 'threads')
    with open(batches_file, 'r') as fh:
        reader = csv.DictReader(itertools.islice(fh, 1, None), fieldnames=fields)
        for line in reader:
            # replace empty strings with None for easier handling by the Batch constructor
            line = {key: value if value != '' else None for key, value in line.items()}
            try:
                batch = Batch(
                    name=line['name'],
                    bucket=line['bucket'],
                    root=line['root'],
                    chunk_size=line['chunk'],
                    storage_class=line['storage'],
                    max_threads=line['threads'],
                    log_dir=line['logs'],
                    mapfile=line['mapfile']
                )
            except ConfigException as e:
                print(e, file=sys.stderr)
                sys.exit(1)

            print(batch.name)
            batch.deposit(s3=get_s3_client(args.profile))
