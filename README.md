# aws-archiver

Command-line preservation archiving tool for S3

## Purpose

The aws-archiver tool is intended to facilitate deposit of assets to Amazon S3
storage while ensuring end-to-end asset fixity and the creation of auditable
deposit records.

## Installation

To install the tool for system-wide access, the recommended method is via pip:

```
$ git clone https://www.github.com/jwestgard/aws-archiver
$ cd aws-archiver && pip install -e .
```

## Usage

The tool is still under development. Currently, there are three modes of making
deposits:

  1. as a single asset specified by the ```-a ASSET``` option; or
  2. as a batch defined in a manifest file specified by the ```-m MAPFILE```
     option; or
  3. as a collection of batches using the ```batch-deposit``` subcommand.

For details on format and creation of batch manifests, see the following section.

### Batch manifest file

Collections of files are loaded using a manifest file. There are two types of
manifest files:

* md5sum manifest files
* patsy-db manifest files

#### md5sum manifest files

A text file listing one asset per line, in the form
```<md5 hash> <whitespace> <absolute local path>```. This is the same line
format as the output of the Unix ```md5sum``` utility.  As a convenience, a
script to generate the latter from a directory of files is included in this
repository's ```bin``` directory.

To create a batch manifest with the included script, do:

```
$ ./bin/make_mapfile.sh path/to/asset/dir mapfile.txt
```

#### patsy-db manifest files

A CSV file listing one asset per line, in the form

```
<md5 hash>,<absolute local path>,<relative path>
```

See the "patsy-db" documentation for information about creating the manifest
file.

### AWS credentials
AWS credentials are required for making deposits. This tool uses the boto3
library to manage authorization using AWS authentication profiles. These
profiles are stored in ```~/.aws/credentials```. To choose a profile to use
with a batch, use the ```-p PROFILE``` option. If left unspecified, the tool
will default to the default profile. The chosen profile must have write
permission for the bucket specified in the ```-b BUCKET``` option.

### Summary of options

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

additional required argument:
  -b BUCKET, --bucket BUCKET     S3 bucket to deposit files into

optional arguments:
  -h, --help                     show this help message and exit
  -c CHUNK, --chunk CHUNK        Chunk size for multipart uploads
  -l LOGS, --logs LOGS           Location to store log files
  -n NAME, --name NAME           Batch identifier or name
  -p PROFILE, --profile PROFILE  AWS authorization profile
  -r ROOT, --root ROOT           Root dir of files being archived
  -s STORAGE, --storage STORAGE  S3 storage class
  -t THREADS, --threads THREADS  Maximum number of concurrent threads
```

### Batch deposit summary

```
usage: archiver batch-deposit [-h] -f BATCHES_FILE [-p PROFILE]

optional arguments:
  -h, --help                        show this help message and exit
  -f BATCHES_FILE, --batches-file   BATCHES_FILE
  -p PROFILE, --profile PROFILE     AWS authorization profile
```

### Default option values

Many of the arguments listed above as "optional" are necessary for the load and
therefore have the following default values:

| option            | default       |
|-------------------|---------------|
| '-c', '--chunk'   | '4GB'         |
| '-l', '--logs'    | 'logs'        |
| '-n', '--name'    | 'test_batch'  |
| '-p', '--profile' | 'default'     |
| '-r', '--root'    | '.'           |
| '-s', '--storage' | 'DEEP_ARCHIVE'|
| '-t', '--threads' | 10            |

## Development Setup

See [docs/DevelopmentSetup.md](docs/DevelopmentSetup.md).
