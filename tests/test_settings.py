# -*- coding: utf-8 -*-
import os
import unittest

from pysmartcache.clients import MemcachedClient, RedisClient
from pysmartcache.engine import CacheEngine, cache
from pysmartcache.exceptions import ImproperlyConfigured
from pysmartcache.settings import PySmartCacheSettings


class SettingsHierarchyTestCase(unittest.TestCase):
    ''' Cache's timeout, backend, host and verbosity are configurable.
        The gold rule is: decorator parameter > PySmartCache settings > OS var > default value.

        | attribute            | decorator parameter  | PySmartCache settings| OS var               | default value        |
        | ---------------------|----------------------|----------------------|----------------------|----------------------|
        | verbose              | verbose              | verbose              | PYSMARTCACHE_VERBOSE | False                |
        | timeout              | timeout              | timeout              | PYSMARTCACHE_TIMEOUT | 3600                 |
        | cache_host           | cache_host           | cache_host           | PYSMARTCACHE_HOST    | ['127.0.0.1:11211', ]|
        | cache_backend        | cache_backend        | cache_backend        | PYSMARTCACHE_BACKEND | 'memcached'          |

    '''

    def tearDown(self):
        super(SettingsHierarchyTestCase, self).tearDown()
        os.environ.pop('PYSMARTCACHE_VERBOSE', None)
        os.environ.pop('PYSMARTCACHE_TIMEOUT', None)
        os.environ.pop('PYSMARTCACHE_HOST', None)
        os.environ.pop('PYSMARTCACHE_BACKEND', None)

        PySmartCacheSettings.reset()

    def test_neither_decorator_parameter_nor_os_var_present(self):
        @cache([])
        def whatever():
            pass

        whatever()
        self.assertEquals(whatever.cache_info_for()['timeout'], 3600)

    def test_decorator_parameter_present(self):
        @cache([], timeout=10)
        def whatever():
            pass

        whatever()
        self.assertEquals(whatever.cache_info_for()['timeout'], 10)

    def test_os_var_present(self):
        @cache([])
        def whatever():
            pass

        os.environ['PYSMARTCACHE_TIMEOUT'] = '20'
        whatever()
        self.assertEquals(whatever.cache_info_for()['timeout'], 20)

    def test_settings_present(self):
        @cache([])
        def whatever():
            pass

        PySmartCacheSettings.timeout = 42
        whatever()
        self.assertEquals(whatever.cache_info_for()['timeout'], 42)

    def test_decorator_parameter_and_os_var_present(self):
        @cache([], timeout=10)
        def whatever():
            pass

        os.environ['PYSMARTCACHE_TIMEOUT'] = '20'
        whatever()
        self.assertEquals(whatever.cache_info_for()['timeout'], 10)

    def test_low_level_timeout(self):
        self.assertEquals(CacheEngine._get_timeout(None), CacheEngine.DEFAULT_TIMEOUT)
        self.assertEquals(CacheEngine._get_timeout(10), 10)

        os.environ['PYSMARTCACHE_TIMEOUT'] = '20'
        self.assertEquals(CacheEngine._get_timeout(None), 20)
        self.assertEquals(CacheEngine._get_timeout(10), 10)

        with self.assertRaises(ImproperlyConfigured) as e:
            os.environ['PYSMARTCACHE_TIMEOUT'] = 'NaN'
            CacheEngine._get_timeout(None)
        self.assertEquals(str(e.exception), 'PYSMARTCACHE_TIMEOUT OS var must be numeric')

        with self.assertRaises(ImproperlyConfigured) as e:
            CacheEngine._get_timeout(-42)
        self.assertEquals(str(e.exception), 'PySmartCache timeout must be positive')

        with self.assertRaises(ImproperlyConfigured) as e:
            CacheEngine._get_timeout(0)
        self.assertEquals(str(e.exception), 'PySmartCache timeout must be positive')

    def test_low_level_cache_backend(self):
        self.assertEquals(CacheEngine._get_cache_backend(None), CacheEngine.DEFAULT_CACHE_BACKEND)
        self.assertEquals(CacheEngine._get_cache_backend('redis'), 'redis')

        os.environ['PYSMARTCACHE_BACKEND'] = 'redis'
        self.assertEquals(CacheEngine._get_cache_backend(None), 'redis')
        self.assertEquals(CacheEngine._get_cache_backend('memcached'), 'memcached')

        with self.assertRaises(ImproperlyConfigured) as e:
            CacheEngine._get_cache_backend('sloth')
        self.assertEquals(str(e.exception), 'PySmartCache type must be one of "memcached", "redis"')

    def test_low_level_hosts_for_memcached(self):
        self.assertEquals(MemcachedClient().get_host(None), MemcachedClient.default_host)
        self.assertEquals(MemcachedClient().get_host(['192.168.0.1:11212', ]), ['192.168.0.1:11212', ])

        os.environ['PYSMARTCACHE_HOST'] = '192.168.0.1:11212,192.168.0.1:11213'
        self.assertEquals(MemcachedClient().get_host(None), ['192.168.0.1:11212', '192.168.0.1:11213'])
        self.assertEquals(MemcachedClient().get_host(['192.168.0.1:11212', ]), ['192.168.0.1:11212', ])

        with self.assertRaises(ImproperlyConfigured) as e:
            MemcachedClient().get_host([])
        self.assertEquals(str(e.exception), 'PySmartCache host can not be empty')

    def test_low_level_hosts_for_redis(self):
        self.assertEquals(RedisClient().get_host(None), RedisClient.default_host)
        self.assertEquals(RedisClient().get_host('192.168.0.1:6378'), '192.168.0.1:6378')

        os.environ['PYSMARTCACHE_HOST'] = '192.168.0.1:6377'
        self.assertEquals(RedisClient().get_host(None), '192.168.0.1:6377')
        self.assertEquals(RedisClient().get_host('192.168.0.1:6378'), '192.168.0.1:6378')

        with self.assertRaises(ImproperlyConfigured) as e:
            RedisClient().get_host('')
        self.assertEquals(str(e.exception), 'PySmartCache host can not be empty')

    def test_low_level_verbose(self):
        self.assertEquals(CacheEngine._get_verbose(None), CacheEngine.DEFAULT_VERBOSE)
        self.assertEquals(CacheEngine._get_verbose(True), True)

        os.environ['PYSMARTCACHE_VERBOSE'] = '1'
        self.assertEquals(CacheEngine._get_verbose(None), True)

        os.environ['PYSMARTCACHE_VERBOSE'] = '0'
        self.assertEquals(CacheEngine._get_verbose(None), False)
        self.assertEquals(CacheEngine._get_verbose(True), True)

        with self.assertRaises(ImproperlyConfigured) as e:
            os.environ['PYSMARTCACHE_VERBOSE'] = 'NaN'
            CacheEngine._get_verbose(None)
        self.assertEquals(str(e.exception), 'PYSMARTCACHE_VERBOSE OS var must be numeric')

        with self.assertRaises(ImproperlyConfigured) as e:
            os.environ['PYSMARTCACHE_VERBOSE'] = '42'
            CacheEngine._get_verbose(None)
        self.assertEquals(str(e.exception), 'PYSMARTCACHE_VERBOSE OS var must be 0 or 1')
