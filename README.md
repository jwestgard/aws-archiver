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
The tool is still under development. Currently, there are two primary modes making a deposit: 
  1. as a single asset specified by the ```-a ASSET``` flag; or 
  2. as a batch defined in a mapfile or manifest listing the md5 hash and local path for each file being deposited (delimited by whitespace). 
  
The latter method's text file format is the same as the output of the UNIX ```md5sum``` utility.  As a convenience, a script to generate the latter from a directory of files is included in this repostiory's ```bin``` directory.

### Batch manifest generation
To create a batch manifest, do:

```
$ ./bin/make_mapfile.sh path/to/asset/dir mapfile.txt
```

### Available parameters

```
S3 preservation archiver

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  Print version number and exit

usage: archiver deposit [-h] -b BUCKET [-c CHUNK] [-l LOGS] [-n NAME]
                        [-p PROFILE] [-r ROOT] [-s STORAGE] [-t THREADS]
                        (-m MAPFILE | -a ASSET)

Deposit a batch of resources to S3

required arguments (choose one):
  -m MAPFILE, --mapfile MAPFILE  Archive assets in inventory file
  -a ASSET, --asset ASSET        Archive a single asset

optional arguments:
  -h, --help                     show this help message and exit
  -b BUCKET, --bucket BUCKET     S3 bucket to deposit files into
  -c CHUNK, --chunk CHUNK        Chunk size for multipart uploads
  -l LOGS, --logs LOGS           Location to store log files
  -n NAME, --name NAME           Batch identifier or name
  -p PROFILE, --profile PROFILE  AWS authorization profile
  -r ROOT, --root ROOT           Root dir of files being archived
  -s STORAGE, --storage STORAGE  S3 storage class
  -t THREADS, --threads THREADS  Maximum number of concurrent threads
```
