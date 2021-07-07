# Development Setup

## Introduction

This page describes how to set up a development environment, and other
information useful for developers to be aware of.

## Prerequisites

The following instructions assume that "pyenv" and "pyenv-virtualenv" are
installed to enable the setup of an isolated Python environment.

See the following for setup instructions:

* <https://github.com/pyenv/pyenv>
* <https://github.com/pyenv/pyenv-virtualenv>

Once "pyenv" and "pyenv-virtualenv" have been installed, install Python 3.7.10:

```
> pyenv install 3.7.10
```

## Installation for development

1) Clone the "aws-archiver" Git repository:

```
> git clone git@github.com:umd-lib/aws-archiver.git
```

2) Switch to the "aws-archiver" directory:

```
> cd aws-archiver
```

3) Set up the virtual environment:

```
> pyenv virtualenv 3.7.10 aws-archiver
> pyenv shell aws-archiver
```

4) Run "pip install", including the "dev" and "test" dependencies:

```
> pip install -e .[dev,test]
```

## Running the Tests

The unit tests for the application can be run using "pytest", i.e.:

```
> pytest
```

**Note:** Currently a deprecation warning related to the "botocore" dependency
is being reported by pytest. To suppress this warning, run:

```
> pytest -p no:warnings
```

## Code Style

Application code style should generally conform to the guidelines in
[PEP 8](https://www.python.org/dev/peps/pep-0008/). The "pycodestyle" tool
to check compliance with the guidelines can be run using:

```
> pycodestyle .
```
