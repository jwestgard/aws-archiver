import csv
import os
import sys

import yaml

from .batch import Batch, DEFAULT_MANIFEST_FILENAME
from .exceptions import ConfigException, FailureException
from .manifests.manifest_factory import ManifestFactory
from .utils import get_first_line


def check_etag(manifest_filename: str) -> bool:
    """
    Determines if etags should be calculated during deposit
    """
    if manifest_filename is None:
        return False

    # The first line has the headers
    header = get_first_line(manifest_filename)
    if 'ETAG' in header:
        return True

    return False


def deposit(args):
    """Deposit a set of files into AWS."""
    try:
        load_single_asset = args.mapfile is None
        manifest = ManifestFactory.create(args.mapfile)
        etag_exists = check_etag(args.mapfile)

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
            manifest.load_manifest(batch.results_filename, batch, etag_exists=etag_exists)

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
    batches_dir = batch_configs['batches_dir'] or os.path.curdir

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
                manifest = ManifestFactory.create(manifest_filename)
                etag_exists = check_etag(args.mapfile)

                batch = Batch(
                    manifest,
                    bucket=config.get('bucket'),
                    asset_root=config.get('asset_root'),
                    name=config.get('name'),
                    log_dir=config.get('logs')
                )
                manifest.load_manifest(config.get('manifest', DEFAULT_MANIFEST_FILENAME), batch,
                                       etag_exists=etag_exists)
            except ConfigException as e:
                print(e, file=sys.stderr)
                raise FailureException from e

            print()
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
