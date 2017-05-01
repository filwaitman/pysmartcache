# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
from distutils.util import strtobool
import hashlib
import inspect
import os
import pickle

from qualname import qualname

from pysmartcache.exceptions import ImproperlyConfigured


def uid(obj):
    return hashlib.md5(pickle.dumps(obj)).hexdigest()


def depth_getattr(root, key):
    if not key:
        return root

    try:
        next_root, next_key = key.split('.', 1)
    except ValueError:
        next_root, next_key = (key, None)

    return depth_getattr(getattr(root, next_root), next_key)


def get_cache_key(func, relevant_keys=None, *args, **kwargs):
    call_args = inspect.getcallargs(func, *args, **kwargs)

    if relevant_keys:
        relevant_values = {}
        for relevant_key in relevant_keys:
            try:
                root, key = relevant_key.split('.', 1)
            except ValueError:
                root, key = (relevant_key, None)

            relevant_values[relevant_key] = depth_getattr(call_args[root], key)

    else:
        relevant_values = call_args

    return '{}-{}'.format(qualname(func), uid(relevant_values))


def get_env_var(var_name, cast=None, default=None):
    env_var_value = os.environ.get(var_name)

    if env_var_value is None:
        return default

    if cast is None:
        return env_var_value

    try:
        if cast == bool:
            return bool(strtobool(env_var_value))
        else:
            return cast(env_var_value)
    except:
        raise ImproperlyConfigured('Var {} could not be casted to type {}'.format(var_name, cast))
