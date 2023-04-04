# Development Setup

## Introduction

This page describes how to set up a development environment, and other
information useful for developers to be aware of.

## Prerequisites

The following instructions assume that "pyenv" is installed to enable the setup of an isolated Python environment.

See the following for setup instructions:

* <https://github.com/pyenv/pyenv>

## Installation for development

1) Clone the "aws-archiver" Git repository:

```bash
> git clone git@github.com:umd-lib/aws-archiver.git
```

2) Switch to the "aws-archiver" directory:

```bash
> cd aws-archiver
```

3) Set up the virtual environment:

```bash
> pyenv install $(cat .python-version)
> pyenv local $(cat .python-version)
> python -m venv .venv --prompt arbitrary-name-for-local-environment
> source .venv/bin/activate
```

4) Run "pip install", including the "dev" and "test" dependencies:

Bash

```bash
> pip install -e .[dev,test]
```

Zsh

```zsh
> pip install -e .'[dev,test]'
```

## Running the Tests

The unit tests for the application can be run using "pytest", i.e.:

```bash
> pytest
```

## Code Style

Application code style should generally conform to the guidelines in
[PEP 8](https://www.python.org/dev/peps/pep-0008/). The "pycodestyle" tool
to check compliance with the guidelines can be run using:

```bash
> pycodestyle .
```
