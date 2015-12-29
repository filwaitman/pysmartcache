# -*- coding: utf-8 -*-
import abc
import pickle

from pysmartcache.exceptions import CacheClientNotFound
from pysmartcache.settings import PySmartCacheSettings


class CacheClient(object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    def all_subclasses(cls):
        return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in s.all_subclasses()]

    @classmethod
    def all_implementations(cls):
        return [x.name for x in cls.all_subclasses()]

    @classmethod
    def instantiate(cls, name, host=None):
        for subclass in cls.all_subclasses():
            if subclass.name == name:
                return subclass(host)
        raise CacheClientNotFound(u'Cache client not found with name "{}". Caches implemented: "{}"'
                                  .format(name, '", "'.join(cls.all_implementations())))

    def __init__(self, host=None):
        cls = self.__class__

        if not hasattr(cls, '_client'):
            if PySmartCacheSettings.cache_client:
                if callable(PySmartCacheSettings.cache_client):
                    cls._client = PySmartCacheSettings.cache_client.im_func()

                else:
                    cls._client = PySmartCacheSettings.cache_client

            else:
                cls._client = self.get_client(host)

        self.client = cls._client

    @abc.abstractmethod
    def get_client(self, host):
        pass

    @abc.abstractmethod
    def get(self, key):
        pass

    @abc.abstractmethod
    def set(self, key, value):
        pass

    @abc.abstractmethod
    def delete(self, key):
        pass

    @abc.abstractmethod
    def purge(self):
        pass


class MemcachedClient(CacheClient):
    _DEFAULT_HOST = ['127.0.0.1:11211', ]
    name = 'memcached'

    def get_client(self, host=None):
        import pylibmc
        host = PySmartCacheSettings._get_cache_host(host, default=self._DEFAULT_HOST, use_list=True)
        return pylibmc.Client(host)

    def get(self, key):
        value = self.client.get(key)
        if value:
            return pickle.loads(value)

    def set(self, key, value):
        self.client.set(key, pickle.dumps(value))

    def delete(self, key):
        self.client.delete(key)

    def purge(self):
        self.client.flush_all()


class RedisClient(CacheClient):
    _DEFAULT_HOST = '127.0.0.1:6379'
    name = 'redis'

    def get_client(self, host=None):
        import redis
        host = PySmartCacheSettings._get_cache_host(host, default=self._DEFAULT_HOST, use_list=False)
        return redis.StrictRedis.from_url(host)

    def get(self, key):
        value = self.client.get(key)
        if value:
            return pickle.loads(value)

    def set(self, key, value):
        self.client.set(key, pickle.dumps(value))

    def delete(self, key):
        self.client.delete(key)

    def purge(self):
        self.client.flushall()
