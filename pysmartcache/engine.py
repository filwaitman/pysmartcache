# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
import os

from pysmartcache.clients import CacheClient
from pysmartcache.constants import CACHE_MISS
from pysmartcache.exceptions import ImproperlyConfigured
from pysmartcache.utils import get_cache_key


class cache(object):
    def __init__(self, keys=None, ttl=None):
        if ttl is None:
            ttl_declared = os.environ.get('PYSMARTCACHE_DEFAULT_TTL')

            if ttl_declared is None:
                ttl = 3600
            elif ttl_declared.isdigit():
                ttl = int(ttl_declared)
            else:
                raise ImproperlyConfigured('PYSMARTCACHE_DEFAULT_TTL must be numeric.')

        self.ttl = ttl
        self.keys = keys

    def get_client(self):
        return CacheClient.instantiate()

    def __call__(self, func):
        def wrapped_f(*args, **kwargs):
            _cache_refresh = kwargs.pop('_cache_refresh', False)
            full_cache_key = get_cache_key(func, self.keys, *args, **kwargs)

            result = self.get_client().get(full_cache_key)
            if (result == CACHE_MISS) or _cache_refresh:
                result = func(*args, **kwargs)
                self.get_client().set(full_cache_key, result, self.ttl)

            return result
        return wrapped_f
