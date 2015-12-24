# -*- coding: utf-8 -*-
import unittest

from pysmartcache.clients import CacheClient, MemcachedClient, RedisClient
from pysmartcache.exceptions import CacheClientNotFound


class CacheClientTestCase(unittest.TestCase):
    def test_get_memcached_client(self):
        client = CacheClient.instantiate('memcached')
        self.assertTrue(isinstance(client, MemcachedClient))

    def test_get_redis_client(self):
        client = CacheClient.instantiate('redis')
        self.assertTrue(isinstance(client, RedisClient))

    def test_get_invalid_client(self):
        with self.assertRaises(CacheClientNotFound) as e:
            CacheClient.instantiate('hamster')
        self.assertEquals(str(e.exception), u'Cache client not found with name "hamster". '
                                            'Caches implemented: "memcached", "redis"')


class CacheClientFunctionalTestCase(object):
    def tearDown(self):
        super(CacheClientFunctionalTestCase, self).tearDown()
        CacheClient.instantiate(self.cache_backend).purge()

    def test_common(self):
        client = CacheClient.instantiate(self.cache_backend)

        self.assertIsNone(client.get('answer'))

        client.set('answer', '42')
        self.assertEquals(client.get('answer'), '42')

        client.set('impulse', '101')
        self.assertEquals(client.get('impulse'), '101')
        self.assertEquals(client.get('answer'), '42')

        client.delete('impulse')
        self.assertIsNone(client.get('impulse'))
        self.assertEquals(client.get('answer'), '42')

        client.purge()
        self.assertIsNone(client.get('impulse'))
        self.assertIsNone(client.get('answer'))


class MemcachedClientFunctionalTestCase(CacheClientFunctionalTestCase, unittest.TestCase):
    cache_backend = 'memcached'


class RedisClientFunctionalTestCase(CacheClientFunctionalTestCase, unittest.TestCase):
    cache_backend = 'redis'
