# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function

from pysmartcache.clients import CacheClient
from pysmartcache.constants import CACHE_MISS
from pysmartcache.utils import get_cache_key, get_env_var


class cache(object):
    def __init__(self, keys=None, ttl=None, cache_exception=None, cache_exception_ttl=None):
        if ttl is None:
            ttl = get_env_var('PYSMARTCACHE_DEFAULT_TTL', int, 3600)

        if cache_exception is None:
            cache_exception = get_env_var('PYSMARTCACHE_DEFAULT_CACHE_EXCEPTION', bool, False)

        if cache_exception_ttl is None:
            cache_exception_ttl = get_env_var('PYSMARTCACHE_DEFAULT_CACHE_EXCEPTION_TTL', int, ttl)

        self.ttl = ttl
        self.keys = keys
        self.cache_exception = cache_exception
        self.cache_exception_ttl = cache_exception_ttl

    def get_client(self):
        return CacheClient.instantiate()

    def __call__(self, func):
        def wrapped_f(*args, **kwargs):
            _cache_refresh = kwargs.pop('_cache_refresh', False)
            full_cache_key = get_cache_key(func, self.keys, *args, **kwargs)
            client = self.get_client()

            cache_value = client.get(full_cache_key)
            if (cache_value == CACHE_MISS) or _cache_refresh:
                try:
                    cache_value = func(*args, **kwargs)
                    ttl = self.ttl
                except Exception as e:
                    if not(self.cache_exception):
                        raise e
                    cache_value = e
                    ttl = self.cache_exception_ttl

                client.set(full_cache_key, cache_value, ttl)

            if isinstance(cache_value, BaseException):
                raise cache_value
            return cache_value

        return wrapped_f
