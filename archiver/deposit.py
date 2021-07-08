import csv
import os
import sys

import yaml

from .batch import Batch, DEFAULT_MANIFEST_FILENAME
from .exceptions import ConfigException, FailureException

from .manifests.md5_sum_manifest import Md5SumManifest
from .manifests.patsy_db_manifest import PatsyDbManifest
from .manifests.single_asset_manifest import SingleAssetManifest


def manifest_factory(manifest_filename):
    """
    Returns the appropriate Manifest implementation for th file
    """
    if manifest_filename is None:
        return SingleAssetManifest(os.path.curdir)
    with open(manifest_filename) as manifest_file:
        # Read the first line
        line = manifest_file.readline().strip()

        if line == "md5,filepath,relpath":
            return PatsyDbManifest(manifest_filename)
        else:
            return Md5SumManifest(manifest_filename)


def deposit(args):
    """Deposit a set of files into AWS."""
    try:
        load_single_asset = args.mapfile is None
        manifest = manifest_factory(args.mapfile)

        batch = Batch(
            manifest,
            name=args.name,
            bucket=args.bucket,
            asset_root=args.root,
            log_dir=args.logs
        )

        if load_single_asset:
            batch.add_asset(args.asset)
        else:
            manifest.load_manifest(batch.results_filename, batch)

    except ConfigException as e:
        print(e, file=sys.stderr)
        raise FailureException from e

    # Do the actual deposit to AWS
    batch.deposit(
        profile_name=args.profile,
        chunk_size=args.chunk,
        storage_class=args.storage,
        max_threads=args.threads,
        dry_run=args.dry_run
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
                manifest_filename = os.path.join(batches_dir, config.get('path'),
                                                 config.get('manifest', DEFAULT_MANIFEST_FILENAME))
                manifest = manifest_factory(manifest_filename)

                batch = Batch(
                    manifest,
                    bucket=config.get('bucket'),
                    asset_root=config.get('asset_root'),
                    name=config.get('name'),
                    log_dir=config.get('logs')
                )
                manifest.load_manifest(config.get('manifest', DEFAULT_MANIFEST_FILENAME), batch)
            except ConfigException as e:
                print(e, file=sys.stderr)
                raise FailureException from e

            print()
            print(f'Batch: {batch.name}')
            batch.deposit(
                profile_name=args.profile,
                chunk_size=config.get('chunk_size'),
                storage_class=config.get('storage_class'),
                max_threads=config.get('max_threads'),
                dry_run=args.dry_run
            )
            writer.writerow(batch.stats)
            for key, value in batch.stats.items():
                print(f"    {key.replace('_', ' ').title()}: {value}")
