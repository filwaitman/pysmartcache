# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
import os
import pickle

from pysmartcache.constants import CACHE_MISS
from pysmartcache.exceptions import ImproperlyConfigured


class CacheClient(object):
    requires_host_configuration = True

    @classmethod
    def all_subclasses(cls):
        return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in s.all_subclasses()]

    @classmethod
    def instantiate(cls):
        client_name = os.environ.get('PYSMARTCACHE_CLIENT', '').upper()

        for subclass in cls.all_subclasses():
            if subclass.name.upper() == client_name:
                if (subclass.requires_host_configuration) and not(cls._get_host()):
                    raise ImproperlyConfigured('PYSMARTCACHE_HOST setting is required for this PYSMARTCACHE_CLIENT.')
                return subclass()

        raise ImproperlyConfigured('Invalid PYSMARTCACHE_CLIENT setting: {}.'.format(client_name))

    @classmethod
    def _get_host(cls):
        return os.environ.get('PYSMARTCACHE_HOST')

    def get(self, key):
        raise NotImplementedError()

    def set(self, key, value, ttl):
        raise NotImplementedError()

    def purge(self):
        raise NotImplementedError()


class DjangoClient(CacheClient):
    requires_host_configuration = False
    name = 'DJANGO'

    def get(self, key):
        from django.core.cache import cache
        return cache.get(key, CACHE_MISS)

    def set(self, key, value, ttl):
        from django.core.cache import cache
        return cache.set(key, value, ttl)

    def purge(self):
        from django.core.cache import cache
        return cache.clear()


class MemcachedClient(CacheClient):
    name = 'MEMCACHED'

    def _get_client(self):
        import pylibmc
        return pylibmc.Client([self._get_host()])

    def get(self, key):
        value = self._get_client().get(key)
        if value:
            return pickle.loads(value)
        return CACHE_MISS

    def set(self, key, value, ttl):
        self._get_client().set(key, pickle.dumps(value), ttl)

    def purge(self):
        self._get_client().flush_all()


class RedisClient(CacheClient):
    name = 'REDIS'

    def _get_client(self):
        import redis
        return redis.StrictRedis.from_url(self._get_host())

    def get(self, key):
        value = self._get_client().get(key)
        if value:
            return pickle.loads(value)
        return CACHE_MISS

    def set(self, key, value, ttl):
        self._get_client().set(key, pickle.dumps(value), ttl)

    def purge(self):
        self._get_client().flushall()
