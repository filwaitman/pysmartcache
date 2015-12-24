# -*- coding: utf-8 -*-
import os
import unittest

from pysmartcache.clients import MemcachedClient, RedisClient
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

    def test_common_verbose(self):
        PySmartCacheSettings.verbose = True
        os.environ['PYSMARTCACHE_VERBOSE'] = '1'

        self.assertTrue(PySmartCacheSettings._get_verbose(True))
        self.assertTrue(PySmartCacheSettings._get_verbose(None))

        PySmartCacheSettings.reset()
        self.assertTrue(PySmartCacheSettings._get_verbose(None))

        os.environ.pop('PYSMARTCACHE_VERBOSE', None)
        self.assertFalse(PySmartCacheSettings._get_verbose(None))

    def test_common_timeout(self):
        PySmartCacheSettings.timeout = 20
        os.environ['PYSMARTCACHE_TIMEOUT'] = '30'

        self.assertEquals(PySmartCacheSettings._get_timeout(10), 10)
        self.assertEquals(PySmartCacheSettings._get_timeout(None), 20)

        PySmartCacheSettings.reset()
        self.assertEquals(PySmartCacheSettings._get_timeout(None), 30)

        os.environ.pop('PYSMARTCACHE_TIMEOUT', None)
        self.assertEquals(PySmartCacheSettings._get_timeout(None), PySmartCacheSettings._DEFAULT_TIMEOUT)

    def test_common_cache_backend(self):
        PySmartCacheSettings.cache_backend = 'redis'
        os.environ['PYSMARTCACHE_BACKEND'] = 'redis'

        self.assertEquals(PySmartCacheSettings._get_cache_backend('redis'), 'redis')
        self.assertEquals(PySmartCacheSettings._get_cache_backend(None), 'redis')

        PySmartCacheSettings.reset()
        self.assertEquals(PySmartCacheSettings._get_cache_backend(None), 'redis')

        os.environ.pop('PYSMARTCACHE_BACKEND', None)
        self.assertEquals(PySmartCacheSettings._get_cache_backend(None), PySmartCacheSettings._DEFAULT_CACHE_BACKEND)

    def test_common_cache_host_memcached(self):
        PySmartCacheSettings.cache_host = ['127.0.0.1:11213', ]
        os.environ['PYSMARTCACHE_HOST'] = '127.0.0.1:11212'

        self.assertEquals(
            PySmartCacheSettings._get_cache_host(['127.0.0.1:11214', ], default=MemcachedClient._DEFAULT_HOST, use_list=True),
            ['127.0.0.1:11214', ]
        )
        self.assertEquals(
            PySmartCacheSettings._get_cache_host(None, default=MemcachedClient._DEFAULT_HOST, use_list=True),
            ['127.0.0.1:11213', ]
        )

        PySmartCacheSettings.reset()
        self.assertEquals(
            PySmartCacheSettings._get_cache_host(None, default=MemcachedClient._DEFAULT_HOST, use_list=True),
            ['127.0.0.1:11212', ]
        )

        os.environ.pop('PYSMARTCACHE_HOST', None)
        self.assertEquals(
            PySmartCacheSettings._get_cache_host(None, default=MemcachedClient._DEFAULT_HOST, use_list=True),
            MemcachedClient._DEFAULT_HOST
        )

    def test_common_cache_host_redis(self):
        PySmartCacheSettings.cache_host = '127.0.0.1:6373'
        os.environ['PYSMARTCACHE_HOST'] = '127.0.0.1:6372'

        self.assertEquals(
            PySmartCacheSettings._get_cache_host('127.0.0.1:6374', default=RedisClient._DEFAULT_HOST, use_list=False),
            '127.0.0.1:6374'
        )
        self.assertEquals(
            PySmartCacheSettings._get_cache_host(None, default=RedisClient._DEFAULT_HOST, use_list=False),
            '127.0.0.1:6373'
        )

        PySmartCacheSettings.reset()
        self.assertEquals(
            PySmartCacheSettings._get_cache_host(None, default=RedisClient._DEFAULT_HOST, use_list=False),
            '127.0.0.1:6372'
        )

        os.environ.pop('PYSMARTCACHE_HOST', None)
        self.assertEquals(
            PySmartCacheSettings._get_cache_host(None, default=RedisClient._DEFAULT_HOST, use_list=False),
            RedisClient._DEFAULT_HOST
        )

    def test_verbose_nan(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_verbose('NaN NaN NaN NaN Batman!')
        self.assertEquals(str(e.exception), 'PySmartCache verbose settings must be numeric')

    def test_verbose_different_from_0_or_1(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_verbose(2)
        self.assertEquals(str(e.exception), 'PySmartCache verbose settings must be 0 or 1')

    def test_timeout_nan(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_timeout('NaN NaN NaN NaN Batman!')
        self.assertEquals(str(e.exception), 'PySmartCache timeout settings must be numeric')

    def test_timeout_negative(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_timeout(-20)
        self.assertEquals(str(e.exception), 'PySmartCache timeout settings must be positive')

    def test_timeout_zero(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_timeout(0)
        self.assertEquals(str(e.exception), 'PySmartCache timeout settings must be positive')

    def test_cache_backend_not_implemented(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_cache_backend('Amazon RDS?!')
        self.assertEquals(str(e.exception), 'PySmartCache cache backend settings must be one of "memcached", "redis"')

    def test_cache_host_boolean_false(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_cache_host('', default='')
        self.assertEquals(str(e.exception), 'PySmartCache cache host settings must not be empty')

        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_cache_host(None, default=None)
        self.assertEquals(str(e.exception), 'PySmartCache cache host settings must not be empty')

        with self.assertRaises(ImproperlyConfigured) as e:
            PySmartCacheSettings._get_cache_host([], default=[])
        self.assertEquals(str(e.exception), 'PySmartCache cache host settings must not be empty')
