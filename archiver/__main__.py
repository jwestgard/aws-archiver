#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import argparse
import sys

from . import version
from .deposit import deposit


def print_header(command):
    """Generate script header and display it in the console."""
    title = f'| AWS Archiver |'
    border = '=' * len(title)
    spacer = '|' + ' '*(len(title)-2) + '|'
    print('\n'.join(['', border, spacer, title, spacer, border, '']))


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
    parser.add_argument('-v', '--version',
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
                        help='S3 bucket to load to'
    )
    deposit_parser.add_argument(
                        '-c', '--chunk',
                        action='store',
                        help='Chunk size for multipart uploads',
                        default='5MB'
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
                        '-s', '--storage',
                        action='store',
                        help='S3 storage class',
                        default='DEEP_ARCHIVE'
    )
    deposit_parser.add_argument(
                        '-t', '--threads',
                        action='store',
                        help='Maximum number of concurrent threads',
                        type=int,
                        default=10
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

    # parse the args and call the default sub-command function
    args = parser.parse_args()
    print_header(args.func.__name__)
    result = args.func(args)


if __name__ == "__main__":
    main()
