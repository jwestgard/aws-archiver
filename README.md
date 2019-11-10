# aws-archiver
Command-line preservation archiving tool for S3

## Purpose
The aws-archiver tool is intended to facilitate deposit of assets to Amazon S3 storage while ensuring end-to-end asset fixity and the creation of auditable deposit records.

## Installation
To install the tool for system-wide access, the recommended method is via pip:
```
$ git clone https://www.github.com/jwestgard/aws-archiver
$ cd aws-archiver && pip install -e .
```

## Usage
The tool is still under development, with full instructions forthcoming.

```
S3 preservation archiver

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  Print version number and exit

subcommands:
  valid subcommands

  {dep}          -h additional help
    deposit (dep)
                 Deposit resources to S3


usage: archiver deposit [-h] -b BUCKET [-c CHUNK] [-s STORAGE] [-n NAME]
                        [-t THREADS] (-m MAPFILE | -a ASSET)

Deposit a batch of resources to S3

optional arguments:
  -h, --help            show this help message and exit
  -b BUCKET, --bucket BUCKET
                        S3 bucket to load to
  -c CHUNK, --chunk CHUNK
                        Chunk size for multipart uploads
  -s STORAGE, --storage STORAGE
                        S3 storage class
  -n NAME, --name NAME  Batch identifier or name
  -t THREADS, --threads THREADS
                        Maximum number of concurrent threads
  -m MAPFILE, --mapfile MAPFILE
                        Archive assets in inventory file
  -a ASSET, --asset ASSET
                        Archive a single asset

```
