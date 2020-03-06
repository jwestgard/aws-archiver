import csv
import os
import sys

import yaml

from .batch import Batch, DEFAULT_MANIFEST_FILENAME
from .exceptions import ConfigException, FailureException


def deposit(args):
    """Deposit a set of files into AWS."""
    try:
        batch = Batch(
            manifest_path=os.path.dirname(args.mapfile) if args.mapfile else os.path.curdir,
            name=args.name,
            bucket=args.bucket,
            asset_root=args.root,
            log_dir=args.logs
        )
        if args.mapfile is not None:
            batch.load_manifest(args.mapfile)
        else:
            batch.add_asset(args.asset)

    except ConfigException as e:
        print(e, file=sys.stderr)
        raise FailureException from e

    # Do the actual deposit to AWS
    batch.deposit(
        profile_name=args.profile,
        chunk_size=args.chunk,
        storage_class=args.storage,
        max_threads=args.threads
    )


STATS_FIELDS = (
    'batch_name',
    'total_assets', 'assets_found', 'assets_missing', 'assets_ignored', 'assets_transmitted', 'asset_bytes_transmitted',
    'successful_deposits', 'failed_deposits', 'deposit_begin', 'deposit_end', 'deposit_time'
)
# symbolic constant for use with open()
LINE_BUFFERING = 1


def batch_deposit(args):
    batches_filename = args.batches_file
    with open(batches_filename, 'r') as batches_file:
        batch_configs = yaml.safe_load(batches_file)
    batches_dir = batch_configs['batches_dir'] or os.path.curdir()

    stats_filename = os.path.join(os.path.dirname(batches_filename), 'stats.csv')
    stats_file_is_new = not os.path.exists(stats_filename)
    with open(stats_filename, mode='a', buffering=LINE_BUFFERING) as stats_file:
        writer = csv.DictWriter(stats_file, fieldnames=STATS_FIELDS)
        if stats_file_is_new:
            writer.writeheader()

        for config in batch_configs['batches']:
            try:
                batch = Batch(
                    manifest_path=os.path.join(batches_dir, config.get('path')),
                    bucket=config.get('bucket'),
                    asset_root=config.get('asset_root'),
                    name=config.get('name'),
                    log_dir=config.get('logs')
                )
                batch.load_manifest(config.get('manifest', DEFAULT_MANIFEST_FILENAME))
            except ConfigException as e:
                print(e, file=sys.stderr)
                raise FailureException from e

            print()
            print(f'Batch: {batch.name}')
            batch.deposit(
                profile_name=args.profile,
                chunk_size=config.get('chunk_size'),
                storage_class=config.get('storage_class'),
                max_threads=config.get('max_threads')
            )
            writer.writerow(batch.stats)
            for key, value in batch.stats.items():
                print(f"    {key.replace('_', ' ').title()}: {value}")
