# Conformance Tests

## Introduction

This document provides a series of tests for verifying the "aws-archiver"
application properly handles various scenarios of upload success and failure.

These tests are intentionally manual, as they perform actual AWS S3 calls, to
an AWS "test" bucket.

## Sample Files

The sample files for the tests are located in the "AwsArchiverTestData" folder
in Box:

<https://umd.app.box.com/folder/205789409677>

## AWS Credentials

The AWS Credentials for the tests are found in the "AWS Archiver Tester"
secure note in "SSDR-Shared" folder in LastPass <https://lastpass.com/>

## AWS Test Bucket

The tests all use the "aws-archiver-test" S3 bucket on the "libr-dev-archive"
account.

## Use of TMP_LOG_DIR for logging

Ideally, the tests should be capable of running in any order, and be as
deterministic as possible. To support this, shell function, `TMP_LOG_DIR` is
used to place the logs in a random subdirectory of the system temporary
directory for each run.

This is needed for deterministic tests because the "deposit" command,
by default, writes out a "results.csv" into a "logs" subdirectory when a file
is successfully uploaded, and then processes any exisitng "results.csv" file
on the next run, skipping uploading files that have already been uploaded.

If a randomized "--logs" parameter is not used, running a "success" test
two times in succession would result in the second run returning a
`Depositing 0 assets ...` response. The same response would occur if a
"success" test for a particular file was followed by a "failure" test for the
same file. This would continue until the "results.csv" file in the "logs"
directory was deleted.

## Test Assumptions

The following tests assume they are being run locally on a Mac OS laptop, using
Bash (commands are also expected to work with Zsh).

## Prerequisites

The following steps will typically only have be performed once to prepare a
workstation to run the tests.

### Prerequisite 1. Install AWS CLI

Install the "AWS Command Line Interface" (AWS CLI) using the instructions at
<https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>

### Prerequisite 2. Setup the AWS Credentials

**Note:** The AWS Credentials for the tests are found in the
"AWS Archiver Tester" secure note in "SSDR-Shared" folder in LastPass
<https://lastpass.com/>

```bash
$ aws configure --profile=aws_archiver_tester
AWS Access Key ID [None]: <"Access Key" from LastPass>
AWS Secret Access Key [None]: <"Secret Access Key" from LastPass>
Defaul region [None]: <Press Enter to accept default>
Default output format [None]: <Press Enter to accept default>
```

This will create an "aws_archiver_tester" AWS profile.

### Prerequisite 3. Download and setup the test data files

Preq-3.1) Download the "AwsArchiveTestData" folder from Box (see "Sample Files"
          above for the location), into the "Downloads" directory of your user
          account. This folder will download as "AwsArchiverTestData.zip"

Preq-3.2) Extract the "AwsArchiverTestData.zip" file:

```bash
$ cd ~/Downloads
$ unzip AwsArchiverTestData.zip
```

Preq-3.3) Create a "/tmp/AwsArchiverTestData" soft link to the extracted
          "AwsArchiverTestData" folder. (This is done because the location
          of the files being uploaded is hard-coded into the CSV files used
          for the tests).

```bash
$ ln -s ~/Downloads/AwsArchiverTestData/ /tmp/AwsArchiverTestData
```

## Test Setup

This following steps set up AWS Archiver and shell environment for the tests.

### 1. Setup aws-archiver

1.1) Clone the "aws-archiver" GitHub repository:

```bash
$ git clone https://github.com/umd-lib/aws-archiver.git
```

1.2) Switch into the "aws-archiver" directory:

```bash
$ cd aws-archiver
```

1.3) (Optional) Switch to the appropriate Git tag/commit.

1.4) Set up the Python environment, using the commands specified in
       [docs/DevelopmentSetup.md](DevelopmentSetup.md).

```bash
$ pyenv install --skip-existing $(cat .python-version)
$ python -m venv .venv --prompt aws-archiver
$ source .venv/bin/activate
```

1.5) Run "pip install", including the "dev" and "test" dependencies:

```zsh
$ pip install -e .'[dev,test]'
```

### 2) Set up the TMP_LOG_DIR function

2.1) Run the following command to create a "TMP_LOG_DIR" shell function to
     generate a random subdirectory for the log:

```bash
$ TMP_LOG_DIR() { echo $TMPDIR`openssl rand -hex 12`; }
```

## Successful Upload Tests

The following tests should all result in successful uploads.

### Tiny File Test (tiny-success.csv)

```bash
$ archiver deposit --profile aws_archiver_tester --bucket aws-archiver-test \
    --mapfile /tmp/AwsArchiverTestData/tiny-success.csv \
    --logs `TMP_LOG_DIR` --root /tmp/AwsArchiverTestData/binaries
```

This should succeed with the following output at the end:

```text
  birds.jpeg -> 13259/13259 (100.00%)

  Upload complete! Verifying...
    -> Local:  7a312012fa894b7c5026a04fed1abfe4
    -> Remote: 7a312012fa894b7c5026a04fed1abfe4

  ETag match! Transfer success!
```

### Less than 4GB Test (LT4GB-success.csv)

```bash
$ archiver deposit --profile aws_archiver_tester --bucket aws-archiver-test \
    --mapfile /tmp/AwsArchiverTestData/LT4GB-success.csv \
    --logs `TMP_LOG_DIR` --root /tmp/AwsArchiverTestData/binaries
```

This should succeed with the following output at the end:

```text
  x633f181q-univarch-024353-0001.mp3 -> 39122207/39122207 (100.00%)

  Upload complete! Verifying...
    -> Local:  76ea279cd332eea7b316f0e0418b0db0
    -> Remote: 76ea279cd332eea7b316f0e0418b0db0

  ETag match! Transfer success!
```

### Greater than 4GB Test (GT4GB-success.csv)

```bash
$ archiver deposit --profile aws_archiver_tester --bucket aws-archiver-test \
    --mapfile /tmp/AwsArchiverTestData/GT4GB-success.csv \
    --logs `TMP_LOG_DIR` --root /tmp/AwsArchiverTestData/binaries
```

This should succeed with the following output at the end:

```text
  mistermen.tar.gz -> 4486091269/4486091269 (100.00%)

  Upload complete! Verifying...
    -> Local:  6129416a2acc31cc6ccce05ce5fdc641-2
    -> Remote: 6129416a2acc31cc6ccce05ce5fdc641-2

  ETag match! Transfer success!
```

## Failed Upload Tests

The following tests should all result in failed uploads.

### Tiny File Test (tiny-failure.csv)

```bash
$ archiver deposit --profile aws_archiver_tester --bucket aws-archiver-test \
    --mapfile /tmp/AwsArchiverTestData/tiny-failure.csv \
    --logs `TMP_LOG_DIR` --root /tmp/AwsArchiverTestData/binaries
```

This should fail with the following output at the end:

```text
  birds.jpeg -> 13259/13259 (100.00%)

  Upload complete! Verifying...
    -> Local:  7a312012fa894b7c5026a04fed1abfe5
    -> Remote: 7a312012fa894b7c5026a04fed1abfe4

  Something went wrong.
```

### Less than 4GB Test (LT4GB-failure.csv)

```bash
$ archiver deposit --profile aws_archiver_tester --bucket aws-archiver-test \
    --mapfile /tmp/AwsArchiverTestData/LT4GB-failure.csv \
    --logs `TMP_LOG_DIR` --root /tmp/AwsArchiverTestData/binaries
```

This should fail with the following output at the end:

```text
  x633f181q-univarch-024353-0001.mp3 -> 39122207/39122207 (100.00%)

  Upload complete! Verifying...
    -> Local:  76ea279cd332eea7b316f0e0418b0db1
    -> Remote: 76ea279cd332eea7b316f0e0418b0db0

  Something went wrong.
```

### Greater than 4GB Test (GT4GB-failure.csv)

```bash
$ archiver deposit --profile aws_archiver_tester --bucket aws-archiver-test \
    --mapfile /tmp/AwsArchiverTestData/GT4GB-failure.csv \
    --logs `TMP_LOG_DIR` --root /tmp/AwsArchiverTestData/binaries
```

This should fail with the following output at the end:

```text
  mistermen.tar.gz -> 4486091269/4486091269 (100.00%)

  Upload complete! Verifying...
    -> Local:  6129416a2acc31cc6ccce05ce5fdc640-2
    -> Remote: 6129416a2acc31cc6ccce05ce5fdc641-2

  Something went wrong.
```
