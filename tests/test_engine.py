# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
import time
import unittest
import uuid

from pysmartcache import cache
from pysmartcache.exceptions import ImproperlyConfigured
from tests.base import override_env

CALLS_COUNT = 0


class Example(object):
    def __init__(self):
        self.id = uuid.uuid4()

    def heavy_calculator(self):
        # Usage of mock.Mock() here for call_count sounds tempting but it doesn't work (can't pickle Mock())
        global CALLS_COUNT
        CALLS_COUNT += 1
        return CALLS_COUNT

    def example_method1(self):
        return self.heavy_calculator()

    def example_method2(self):
        return self.heavy_calculator()

    def example_method3(self, a, b, c=None):
        return self.heavy_calculator()

    def example_method4(self, a, b, c=None):
        return self.heavy_calculator()


class CacheTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env_vars = {
            'PYSMARTCACHE_CLIENT': 'REDIS',
            'PYSMARTCACHE_HOST': '127.0.0.1:6379',
            'PYSMARTCACHE_DEFAULT_TTL': 2,
        }

        with override_env(**cls.env_vars):
            Example.example_method1 = cache(ttl=1)(Example.example_method1)
            Example.example_method2 = cache()(Example.example_method2)
            Example.example_method3 = cache(ttl=1)(Example.example_method3)
            Example.example_method4 = cache(keys=['self.id', 'a'])(Example.example_method4)

    def test_ttl_must_be_numeric(self):
        bad_env_vars = self.env_vars.copy()
        bad_env_vars['PYSMARTCACHE_DEFAULT_TTL'] = 'XXX'

        with override_env(**bad_env_vars):
            with self.assertRaises(ImproperlyConfigured):
                Example.example_method1 = cache()(Example.example_method1)

    def test_common(self):
        with override_env(**self.env_vars):
            example = Example()
            global CALLS_COUNT
            CALLS_COUNT = 0

            example.example_method1()
            self.assertEquals(CALLS_COUNT, 1)

            example.example_method1()
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit.

            time.sleep(0.5)
            example.example_method1()
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit.

            time.sleep(0.6)
            example.example_method1()
            self.assertEquals(CALLS_COUNT, 2)  # Cache miss.

            example.example_method1()
            self.assertEquals(CALLS_COUNT, 2)  # Cache hit.

            example.example_method1(_cache_refresh=False)
            self.assertEquals(CALLS_COUNT, 2)  # Cache hit.

            example.example_method1(_cache_refresh=True)
            self.assertEquals(CALLS_COUNT, 3)  # Cache would hit, but we wanted it refreshed.

    def test_default_cache_ttl(self):
        with override_env(**self.env_vars):
            example = Example()
            global CALLS_COUNT
            CALLS_COUNT = 0

            example.example_method2()
            self.assertEquals(CALLS_COUNT, 1)

            example.example_method2()
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit.

            time.sleep(1)
            example.example_method2()
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit.

            time.sleep(1.1)
            example.example_method2()
            self.assertEquals(CALLS_COUNT, 2)  # Cache miss.

    def test_multiple_arguments(self):
        with override_env(**self.env_vars):
            example = Example()
            global CALLS_COUNT
            CALLS_COUNT = 0

            example.example_method3(1, 1)
            self.assertEquals(CALLS_COUNT, 1)

            example.example_method3(1, 1)
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit.

            example.example_method3(1, 1, None)
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit.

            example.example_method3(1, 2, None)
            self.assertEquals(CALLS_COUNT, 2)  # Cache miss.

            example.example_method3(1, 1, None)
            self.assertEquals(CALLS_COUNT, 2)  # Cache hit.

            example.example_method3(1, 1, 0)
            self.assertEquals(CALLS_COUNT, 3)  # Cache miss.

            example.example_method3(1, 1, 0)
            self.assertEquals(CALLS_COUNT, 3)  # Cache hit.

            time.sleep(1.1)
            example.example_method3(1, 1, 0)
            self.assertEquals(CALLS_COUNT, 4)  # Cache miss.

    def test_relevant_keys(self):
        with override_env(**self.env_vars):
            example1 = Example()
            example2 = Example()
            global CALLS_COUNT
            CALLS_COUNT = 0

            example1.example_method4(1, 1)
            self.assertEquals(CALLS_COUNT, 1)

            example1.example_method4(1, 2)
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit: only 'a' argument matters.

            example1.example_method4(1, 3, c=24)
            self.assertEquals(CALLS_COUNT, 1)  # Cache hit: only 'a' argument matters.

            example2.example_method4(1, 1)
            self.assertEquals(CALLS_COUNT, 2)  # Cache miss: (example2, not example1).

            example2.whatever = 'whatever'
            example2.example_method4(1, 1)
            self.assertEquals(CALLS_COUNT, 2)  # Cache hit.

            example2.id = uuid.uuid4()
            example2.example_method4(1, 1)
            self.assertEquals(CALLS_COUNT, 3)  # Cache miss.
