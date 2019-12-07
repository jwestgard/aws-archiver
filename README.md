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
The tool is still under development. Currently, there are two primary modes of making deposits: 
  1. as a single asset specified by the ```-a ASSET``` option; or 
  2. as a batch defined in a manifest file specified by the ```-m MAPFILE``` option.

For details on format and creation of batch manifests, see the following section.

### Batch manifest file
Collections of files are loaded using a manifest file. The format of the manifest is a text file listing one asset per line, in the form ```<md5 hash> <whitespace> <absolute local path>```. This is the same line format as the output of the Unix ```md5sum``` utility.  As a convenience, a script to generate the latter from a directory of files is included in this repository's ```bin``` directory.

To create a batch manifest with the included script, do:
```
$ ./bin/make_mapfile.sh path/to/asset/dir mapfile.txt
```

### AWS credentials
AWS credentials are required for making deposits. This tool uses the boto3 library to manage authorization using AWS authentication profiles. These profiles are stored in ```~/.aws/credentials```. To choose a profile to use with a batch, use the ```-p PROFILE``` option. If left unspecified, the tool will default to the default profile. The chosen profile must have write permission for the bucket specified in the ```-b BUCKET``` option.

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

### Default option values
Many of the arguments listed above as "optional" are necessary for the load and therefore have the following default values:

| option            | default       |
|-------------------|---------------|
| '-c', '--chunk'   | '5MB'         |
| '-l', '--logs'    | 'logs'        |
| '-n', '--name'    | 'test_batch'  |
| '-p', '--profile' | 'default'     |
| '-r', '--root'    | '.'           |
| '-s', '--storage' | 'DEEP_ARCHIVE'|
| '-t', '--threads' | 10            |
  
## Known issues
This relative path caluclulation problem has now been described in [issue #3](https://github.com/jwestgard/aws-archiver/issues/3).

## Development roadmap
To facilitate loading large quantities of assets (i.e. multiple batches), a "batch of batches" mode will be added. This will provide the ability to define a set of batches in a CSV file containing the path to each batch manifest file as well as the values to use for each batch's options.
