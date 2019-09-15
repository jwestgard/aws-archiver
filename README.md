# aws-archiver
Command-line preservation archiving tool for S3

## Purpose
The aws-archiver tool is intended to facilitate deposit of assets to Amazon S3 storage while ensuring end-to-end asset fixity and the creation of a auditable deposit records.

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
```
