#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import os
import sys

from . import version, batch
from .deposit import deposit, batch_deposit
from .exceptions import FailureException


STATS_FIELDS = (
    'total_assets', 'assets_found', 'assets_missing', 'assets_ignored', 'assets_transmitted', 'asset_bytes_transmitted',
    'successful_deposits', 'failed_deposits', 'deposit_begin', 'deposit_end', 'deposit_time'
)


def print_header():
    """Generate script header and display it in the console."""
    title = f'| AWS Archiver |'
    border = '=' * len(title)
    spacer = '|' + ' '*(len(title)-2) + '|'
    sys.stdout.write(
        '\n'.join(['', border, spacer, title, spacer, border, '', ''])
    )


def main():
    """Parse args and set the chosen sub-command as the default function."""

    # main parser for command line arguments
    parser = argparse.ArgumentParser(description='S3 preservation archiver')
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        help='-h additional help',
        metavar='{dep}',
        dest='cmd'
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        help='Print version number and exit',
        version=version
    )

    subparsers.required = True

    # argument parser for the deposit sub-command
    deposit_parser = subparsers.add_parser(
        'deposit', aliases=['dep'],
        help='Deposit resources to S3',
        description='Deposit a batch of resources to S3'
    )
    deposit_parser.add_argument(
        '-b', '--bucket',
        action='store',
        required=True,
        help='S3 bucket to deposit files into'
    )
    deposit_parser.add_argument(
        '-c', '--chunk',
        action='store',
        help='Chunk size for multipart uploads',
        default=batch.DEFAULT_CHUNK_SIZE
    )
    deposit_parser.add_argument(
        '-l', '--logs',
        action='store',
        help='Location to store log files',
        default=batch.DEFAULT_LOG_DIR
    )
    deposit_parser.add_argument(
        '-n', '--name',
        action='store',
        help='Batch identifier or name',
        default='test_batch'
    )
    deposit_parser.add_argument(
        '-p', '--profile',
        action='store',
        help='AWS authorization profile',
        default='default'
    )
    deposit_parser.add_argument(
        '-r', '--root',
        action='store',
        help='Root dir of files being archived',
        default='.'
    )
    deposit_parser.add_argument(
        '-s', '--storage',
        action='store',
        help='S3 storage class',
        default=batch.DEFAULT_STORAGE_CLASS
    )
    deposit_parser.add_argument(
        '-t', '--threads',
        action='store',
        help='Maximum number of concurrent threads',
        type=int,
        default=batch.DEFAULT_MAX_THREADS
    )

    # argument parser for specifying the asset or list of assets to deposit
    files_group = deposit_parser.add_mutually_exclusive_group(required=True)
    files_group.add_argument(
        '-m', '--mapfile',
        action='store',
        help='Archive assets in inventory file'
    )
    files_group.add_argument(
        '-a', '--asset',
        action='store',
        help='Archive a single asset'
    )

    deposit_parser.set_defaults(func=deposit)

    batch_deposit_parser = subparsers.add_parser('batch-deposit')
    batch_deposit_parser.add_argument(
        '-f', '--batches-file',
        action='store',
        required=True
    )
    batch_deposit_parser.add_argument(
        '-p', '--profile',
        action='store',
        help='AWS authorization profile',
        default='default'
    )

    batch_deposit_parser.set_defaults(func=batch_deposit)

    # parse the args and call the default sub-command function
    # sub-command functions are expected to return a generator
    # that yields a Batch object
    args = parser.parse_args()
    print_header()
    # TODO: configurable stats_filename
    stats_filename = 'stats.csv'
    is_new = not os.path.exists(stats_filename)
    with open(stats_filename, 'a') as stats_file:
        writer = csv.DictWriter(stats_file, fieldnames=STATS_FIELDS)
        if is_new:
            writer.writeheader()
        try:
            for batch_obj in args.func(args):
                writer.writerow(batch_obj.stats)
                print()
                print(f'Batch Name: {batch_obj.name}')
                for key, value in batch_obj.stats.items():
                    print(f"    {key.replace('_', ' ').title()}: {value}")
        except FailureException:
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(2)


if __name__ == "__main__":
    main()
