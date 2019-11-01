#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import argparse
import sys

from . import version
from .deposit import deposit

def main():

    '''Parse args and set the chosen sub-command as the default function.'''

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

    # argument parsers for various sub-commands
    deposit_parser = subparsers.add_parser(
                        'deposit', aliases=['dep'], 
                        help='Deposit resources to S3',
                        description='Deposit a batch of resources to S3'
    )
    
    # facility for loading a list of files
    deposit_parser.add_argument(
                        '-m', '--mapfile',
                        action='store',
                        help='Archive assets in inventory file'
    )
    
    # facility for loading a single file
    deposit_parser.add_argument(
                        '-a', '--asset',
                        action='store',
                        help='Archive a single asset'
    )
    
    deposit_parser.set_defaults(func=deposit)

    # parse the args and call the default sub-command function
    args = parser.parse_args()
    result = args.func(args)


if __name__ == "__main__":
    main()
