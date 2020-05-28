[![Travis](https://travis-ci.com/filwaitman/pysmartcache.svg?branch=master)](https://travis-ci.com/filwaitman/pysmartcache)
[![Codecov](https://codecov.io/gh/filwaitman/pysmartcache/branch/master/graph/badge.svg)](https://codecov.io/gh/filwaitman/pysmartcache)
[![PyPI](https://img.shields.io/pypi/v/pysmartcache.svg)](https://pypi.python.org/pypi/pysmartcache/)
[![License](https://img.shields.io/pypi/l/pysmartcache.svg)](https://pypi.python.org/pypi/pysmartcache/)
[![Python versions](https://img.shields.io/pypi/pyversions/pysmartcache.svg)](https://pypi.python.org/pypi/pysmartcache/)
[![PyPI downloads per month](https://img.shields.io/pypi/dm/pysmartcache.svg)](https://pypi.python.org/pypi/pysmartcache/)


# pysmartcache

Automatic caching and caching invalidation for callables


## Development:

### Run linter:
```bash
pip install -r requirements_dev.txt
isort -rc .
tox -e lint
```

### Run tests via `tox`:
```bash
pip install -r requirements_dev.txt
tox
```

### Release a new major/minor/patch version:
```bash
pip install -r requirements_dev.txt
bump2version <PART>  # <PART> can be either 'patch' or 'minor' or 'major'
```

### Upload to PyPI:
```bash
pip install -r requirements_dev.txt
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```

## Contributing:

Please [open issues](https://github.com/filwaitman/pysmartcache/issues) if you see one, or [create a pull request](https://github.com/filwaitman/pysmartcache/pulls) when possible.
In case of a pull request, please consider the following:
- Respect the line length (132 characters)
- Write automated tests
- Run `tox` locally so you can see if everything is green (including linter and other python versions)
