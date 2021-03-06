import os
from contextlib import contextmanager


@contextmanager
def override_env(**overrides):
    def _load_env(d):
        for key, value in d.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)

    originals = {}
    for key, value in overrides.items():
        originals[key] = os.environ.get(key)

    _load_env(overrides)

    try:
        yield
    finally:
        _load_env(originals)
