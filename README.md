
# GraphKB (Python)

![build](https://github.com/bcgsc/pori_graphkb_python/workflows/build/badge.svg) [![PyPi](https://img.shields.io/pypi/v/graphkb.svg)](https://pypi.org/project/graphkb) [![codecov](https://codecov.io/gh/bcgsc/pori_graphkb_python/branch/master/graph/badge.svg)](https://codecov.io/gh/bcgsc/pori_graphkb_python) [![PyPI - Downloads](https://img.shields.io/pypi/dm/graphkb)](https://pypistats.org/packages/graphkb) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5730523.svg)](https://doi.org/10.5281/zenodo.5730523)

This repository is part of the [platform for oncogenomic reporting and interpretation](https://github.com/bcgsc/pori).

Python adapter package for querying the GraphKB API. See the [user manual](https://bcgsc.github.io/pori/graphkb/scripting/)

- [Getting Started](#getting-started)
  - [Install (For developers)](#install-for-developers)
  - [Run Tests](#run-tests)
- [Generating the Documentation](#generating-the-documentation)
- [Deployment (Publishing)](#deployment-publishing)

## Getting Started

### Install (For developers)

clone this repository

```bash
git clone https://github.com/bcgsc/pori_graphkb_python
cd pori_graphkb_python
```

create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

install the package and its development dependencies

```bash
pip install -U pip setuptools
pip install -e .[dev]
```

### Run Tests

```bash
pytest tests
```

## Generating the Documentation

User documentation for this repository is hosted in the [central PORI repository](https://github.com/bcgsc/pori/)

## Deployment (Publishing)

Install the deployment dependencies

```bash
pip install .[deploy]
```

Build the distribution files

```bash
python setup.py install sdist bdist_wheel
```

Upload the distibutions to the package server (`-r` is defined in your pypirc)

```bash
twine upload -r bcgsc dist/*
```
