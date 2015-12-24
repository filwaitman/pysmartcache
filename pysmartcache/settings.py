# -*- coding: utf-8 -*-
import os

from pysmartcache.exceptions import ImproperlyConfigured


class PySmartCacheSettings(object):
    __slots__ = ['verbose', 'timeout', 'cache_backend', 'cache_host', ]

    verbose = None
    timeout = None
    cache_backend = None
    cache_host = None

    _DEFAULT_VERBOSE = False
    _DEFAULT_TIMEOUT = 3600
    _DEFAULT_CACHE_BACKEND = 'memcached'

    @classmethod
    def reset(cls):
        for attr in cls.__slots__:
            setattr(cls, attr, None)

    @classmethod
    def _get_verbose(cls, verbose):
        if verbose is None:
            verbose = PySmartCacheSettings.verbose

        if verbose is None:
            verbose = os.environ.get('PYSMARTCACHE_VERBOSE')

        if verbose is None:
            verbose = cls._DEFAULT_VERBOSE

        if not isinstance(verbose, bool):
            try:
                verbose = int(verbose)
            except:
                raise ImproperlyConfigured('PySmartCache verbose settings must be numeric')
            if verbose not in (0, 1):
                raise ImproperlyConfigured('PySmartCache verbose settings must be 0 or 1')

        return verbose

    @classmethod
    def _get_timeout(cls, timeout):
        if timeout is None:
            timeout = PySmartCacheSettings.timeout

        if timeout is None:
            timeout = os.environ.get('PYSMARTCACHE_TIMEOUT')

        if timeout is None:
            timeout = cls._DEFAULT_TIMEOUT

        try:
            timeout = int(timeout)
        except:
            raise ImproperlyConfigured('PySmartCache timeout settings must be numeric')
        if timeout <= 0:
            raise ImproperlyConfigured('PySmartCache timeout settings must be positive')

        return timeout

    @classmethod
    def _get_cache_backend(cls, cache_backend):
        from pysmartcache.clients import CacheClient

        client_implementations = CacheClient.all_implementations()

        if cache_backend is None:
            cache_backend = PySmartCacheSettings.cache_backend

        if cache_backend is None:
            cache_backend = os.environ.get('PYSMARTCACHE_BACKEND')

        if cache_backend is None:
            cache_backend = cls._DEFAULT_CACHE_BACKEND

        if cache_backend not in client_implementations:
            raise ImproperlyConfigured('PySmartCache cache backend settings must be one of "{}"'
                                       .format('", "'.join(client_implementations)))

        return cache_backend

    @classmethod
    def _get_cache_host(cls, host, default, use_list=True):
        if host is None:
            host = PySmartCacheSettings.cache_host

        if host is None:
            host = os.environ.get('PYSMARTCACHE_HOST')

        if host is None:
            host = default

        if not host:
            raise ImproperlyConfigured('PySmartCache cache host settings must not be empty')

        if use_list:
            if isinstance(host, basestring):
                host = host.split(',')
            else:
                host = list(host)

        return host
