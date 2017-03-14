# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
import unittest
import time

from pysmartcache.clients import CacheClient, RedisClient, MemcachedClient, DjangoClient
from pysmartcache.constants import CACHE_MISS
from pysmartcache.exceptions import ImproperlyConfigured
from tests.base import override_env


class CacheClientTestCase(unittest.TestCase):
    def test_instantiate(self):
        with override_env(PYSMARTCACHE_CLIENT='REDIS', PYSMARTCACHE_HOST='127.0.0.1:6379'):
            client = CacheClient.instantiate()
            self.assertTrue(isinstance(client, RedisClient))

        with override_env(PYSMARTCACHE_CLIENT='MEMCACHED', PYSMARTCACHE_HOST='127.0.0.1:11211'):
            client = CacheClient.instantiate()
            self.assertTrue(isinstance(client, MemcachedClient))

        with override_env(PYSMARTCACHE_CLIENT='DJANGO'):
            client = CacheClient.instantiate()
            self.assertTrue(isinstance(client, DjangoClient))

        with override_env(PYSMARTCACHE_CLIENT='django'):
            client = CacheClient.instantiate()
            self.assertTrue(isinstance(client, DjangoClient))

        with override_env(PYSMARTCACHE_CLIENT='dJaNgO'):
            client = CacheClient.instantiate()
            self.assertTrue(isinstance(client, DjangoClient))

        with override_env(PYSMARTCACHE_CLIENT=None):  # This is mandatory.
            self.assertRaises(ImproperlyConfigured, CacheClient.instantiate)

        with override_env(PYSMARTCACHE_CLIENT='HAMSTER', PYSMARTCACHE_HOST='1.1.1.1'):  # Invalid client.
            self.assertRaises(ImproperlyConfigured, CacheClient.instantiate)

        with override_env(PYSMARTCACHE_CLIENT='REDIS'):  # Host is mandatory for REDIS.
            self.assertRaises(ImproperlyConfigured, CacheClient.instantiate)

        with override_env(PYSMARTCACHE_CLIENT='MEMCACHED'):  # Host is mandatory for MEMCACHED.
            self.assertRaises(ImproperlyConfigured, CacheClient.instantiate)


class ClientBaseTestCase(object):
    def tearDown(self):
        with override_env(PYSMARTCACHE_CLIENT=self.client_name, PYSMARTCACHE_HOST=self.client_host):
            super(ClientBaseTestCase, self).tearDown()
            CacheClient.instantiate().purge()

    def test_common(self):
        with override_env(PYSMARTCACHE_CLIENT=self.client_name, PYSMARTCACHE_HOST=self.client_host):
            client = CacheClient.instantiate()

            self.assertEqual(client.get('answer'), CACHE_MISS)

            client.set('answer', '42', 1)
            self.assertEqual(client.get('answer'), '42')

            client.set('impulse', '101', 3)
            self.assertEqual(client.get('impulse'), '101')
            self.assertEqual(client.get('answer'), '42')

            time.sleep(1)
            self.assertEqual(client.get('impulse'), '101')
            self.assertEqual(client.get('answer'), CACHE_MISS)  # Expired

            client.purge()
            self.assertEqual(client.get('impulse'), CACHE_MISS)
            self.assertEqual(client.get('answer'), CACHE_MISS)


class RedisClientTestCase(ClientBaseTestCase, unittest.TestCase):
    client_name = 'REDIS'
    client_host = '127.0.0.1:6379'


class MemcachedClientTestCase(ClientBaseTestCase, unittest.TestCase):
    client_name = 'MEMCACHED'
    client_host = '127.0.0.1:11211'
