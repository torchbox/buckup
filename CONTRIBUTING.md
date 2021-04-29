# Contributing

## Install

To make changes to this project, first clone this repository:

```sh
git clone git@github.com:torchbox/buckup.git
cd buckup
```

With your preferred virtualenv activated, install testing dependencies:

```sh
pip install -e .
```

## Releases

First make sure to update the version number in `setup.cfg` and the CHANGELOG. Then,

```sh
pip install wheel twine
rm -rf dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
```
