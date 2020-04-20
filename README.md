
# GraphKB (Python)

Python adapter package for querying the GraphKB API

- [Getting Started](#getting-started)
  - [Install (For developers)](#install-for-developers)
  - [Run Tests](#run-tests)
- [Generating the Documentation](#generating-the-documentation)
- [Deployment (Publishing)](#deployment-publishing)

## Getting Started

### Install (For developers)

clone this repository

```
git clone ssh://git@svn.bcgsc.ca:7999/dat/graphkb_python.git
cd knowledgebase_match
```

create a virtual environment

```
python3 -m venv venv
source venv/bin/activate
```

install the package and its development dependencies

```
pip install -e .[dev]
```

### Run Tests

```
pytest tests
```

## Generating the Documentation

This documentation is generated using [mkdocs](https://www.mkdocs.org), [mkdocs-material](https://pypi.org/project/mkdocs-material), and [markdown_refdocs](https://pypi.org/project/markdown-refdocs).

First install the documentation dependencies

```bash
pip install .[doc]
```

Then generate the user manual files

```bash
markdown_refdocs graphkb -o docs/reference
mkdocs build
```

There should now be static html files under `build-docs`. To view the files, serve the folder using
the built-in python http server

```bash
python3 -m http.server -d build-docs
```

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
