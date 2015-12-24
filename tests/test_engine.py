# -*- coding: utf-8 -*-
import datetime
import os
import unittest

from freezegun import freeze_time
import mock

from pysmartcache.clients import CacheClient, MemcachedClient, RedisClient
from pysmartcache.engine import CacheEngine, cache
from pysmartcache.exceptions import ImproperlyConfigured

CACHE_TIMEOUT = 10
CACHE_VERBOSE = False


@cache(['a', 'b'], timeout=CACHE_TIMEOUT, verbose=CACHE_VERBOSE)
def kinda_sum(a, b, useless_parameter_for_cache=None):
    return a + b


class AnotherClass(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b


class KindaSumClass(object):
    def __init__(self, a, b, useless_parameter_for_cache=None, child=None):
        self.a = a
        self.b = b
        self.useless_parameter_for_cache = useless_parameter_for_cache
        self.child = child

    @cache(['self.a', 'self.b'], timeout=CACHE_TIMEOUT, verbose=CACHE_VERBOSE)
    def just_do_it(self):
        return self.a + self.b

    @cache(['self.a', 'self.b', 'self.child.a'], timeout=CACHE_TIMEOUT, verbose=CACHE_VERBOSE)
    def depending_on_child(self):
        return self.a + self.b + self.child.a


class CacheCommonTestCase(object):
    def setUp(self):
        super(CacheCommonTestCase, self).setUp()

        os.environ['PYSMARTCACHE_BACKEND'] = self.cache_backend
        CacheClient.instantiate(self.cache_backend).purge()
        self.now = datetime.datetime.utcnow()

        self._patch1 = mock.patch.object(CacheEngine, '_cache_hit_signal')
        self.cache_hit_patched = self._patch1.start()
        self._patch2 = mock.patch.object(CacheEngine, '_cache_outdated_signal')
        self.cache_outdated_patched = self._patch2.start()
        self._patch3 = mock.patch.object(CacheEngine, '_cache_missed_signal')
        self.cache_missed_patched = self._patch3.start()
        self.mocks = [self._patch1, self._patch2, self._patch3]

    def tearDown(self):
        super(CacheCommonTestCase, self).tearDown()

        os.environ.pop('PYSMARTCACHE_BACKEND', None)
        for mock_ in self.mocks:
            mock_.stop()

    def test_missed_hit(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

    def test_missed_outdated(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

        with freeze_time(self.now + datetime.timedelta(seconds=60)):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

    def test_missed_missed(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

    def test_sequence(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 2)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

    def test_cache_purge(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            CacheClient.instantiate(self.cache_backend).purge()

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 3)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 4)

    def test_cache_invalidate(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            kinda_sum.cache_invalidate_for(2, 4)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 3)

    def test_cache_info(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

        with freeze_time(self.now + datetime.timedelta(seconds=3)):
            info = kinda_sum.cache_info_for(2, 3)
            self.assertEquals(info['value'], 5)
            self.assertEquals(info['date added'], self.now)
            self.assertEquals(info['outdated'], False)
            self.assertEquals(info['timeout'], 10)
            self.assertEquals(info['age'], 3)

        with freeze_time(self.now + datetime.timedelta(seconds=13)):
            info = kinda_sum.cache_info_for(2, 3)
            self.assertEquals(info['value'], 5)
            self.assertEquals(info['date added'], self.now)
            self.assertEquals(info['outdated'], True)
            self.assertEquals(info['timeout'], 10)
            self.assertEquals(info['age'], 13)

    def test_cache_refresh(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)
            self.assertEquals(kinda_sum.cache_info_for(2, 3)['date added'], self.now)

        with freeze_time(self.now + datetime.timedelta(seconds=5)):
            result = kinda_sum.cache_refresh_for(2, 3)

            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)
            self.assertEquals(kinda_sum.cache_info_for(2, 3)['date added'], self.now + datetime.timedelta(seconds=5))

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)
            self.assertEquals(kinda_sum.cache_info_for(2, 3)['date added'], self.now + datetime.timedelta(seconds=5))

    def test_only_declared_keys_matter_for_cache_sake(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=None)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=42)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=True)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

    def test_methods_decorated_inside_classes_work_exactly_the_same_way(self):
        with freeze_time(self.now):
            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 2)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

    def test_deep_attribute_changed_on_keys_affect_cache(self):
        with freeze_time(self.now):
            child = AnotherClass(a=2, b=10)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 7)

            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            child = AnotherClass(a=2, b=10)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 7)

            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            child = AnotherClass(a=2, b=10000)  # b doesn't matter for this cache
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 7)

            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 1)

            child = AnotherClass(a=37, b=10000)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 42)

            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_missed_patched.call_count, 2)

    def test_raise_exception_properly(self):
        @cache(['a', 'b'], timeout=CACHE_TIMEOUT, verbose=CACHE_VERBOSE)
        def kinda_sum_broken(a, b, useless_parameter_for_cache=None):
            return a + b / 0

        @cache(['a', 'b'], timeout=CACHE_TIMEOUT, verbose=CACHE_VERBOSE)
        def kinda_sum_broken2(a, b, useless_parameter_for_cache=None):
            return a + b.wild_attr

        with self.assertRaises(ZeroDivisionError) as e:
            kinda_sum_broken(2, 3)
        self.assertEquals(str(e.exception), 'integer division or modulo by zero')

        with self.assertRaises(AttributeError) as e:
            kinda_sum_broken2(2, 3)
        self.assertEquals(str(e.exception), "'int' object has no attribute 'wild_attr'")


class MemcachedClientEngineTestCase(CacheCommonTestCase, unittest.TestCase):
    cache_backend = 'memcached'


class RedisClientEngineTestCase(CacheCommonTestCase, unittest.TestCase):
    cache_backend = 'redis'


class SettingsHierarchyTestCase(unittest.TestCase):
    ''' Cache's timeout, hosts and verbosity are configurable. The gold rule is: decorator parameter > OS var > default.

        | attribute name           | decorator parameter name | OS var name              | default value            |
        | -------------------------|--------------------------|--------------------------|--------------------------|
        | timeout                  | timeout                  | PYSMARTCACHE_TIMEOUT     | 3600                     |
        | verbose                  | verbose                  | PYSMARTCACHE_VERBOSE     | False                    |
        | hosts                    | hosts                    | PYSMARTCACHE_HOSTS       | ['127.0.0.1:11211', ]    |

    '''

    def tearDown(self):
        super(SettingsHierarchyTestCase, self).tearDown()
        os.environ.pop('PYSMARTCACHE_TIMEOUT', None)
        os.environ.pop('PYSMARTCACHE_HOST', None)
        os.environ.pop('PYSMARTCACHE_VERBOSE', None)

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

    def test_low_level_type(self):
        self.assertEquals(CacheEngine._get_type(None), CacheEngine.DEFAULT_TYPE)
        self.assertEquals(CacheEngine._get_type('redis'), 'redis')

        os.environ['PYSMARTCACHE_BACKEND'] = 'redis'
        self.assertEquals(CacheEngine._get_type(None), 'redis')
        self.assertEquals(CacheEngine._get_type('memcached'), 'memcached')

        with self.assertRaises(ImproperlyConfigured) as e:
            CacheEngine._get_type('sloth')
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


class CacheKeysTestCase(unittest.TestCase):
    def test_neither_include_nor_exclude(self):
        @cache()
        def this_is_a_thing(a, b, c):
            return a + b + c

        self.assertEquals(this_is_a_thing.cache_keys_included, [])
        self.assertEquals(this_is_a_thing.cache_keys_excluded, [])
        self.assertEquals(this_is_a_thing.cache_keys, ['a', 'b', 'c'])

    def test_both_include_and_exclude(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            @cache(include=['a', ], exclude=['a', ])
            def this_is_a_thing(a, b, c):
                return a + b + c
        self.assertEquals(str(e.exception), 'You shall not provide both include and exclude arguments')

    def test_include(self):
        @cache(include=['a', ])
        def this_is_a_thing(a, b, c):
            return a + b + c

        self.assertEquals(this_is_a_thing.cache_keys_included, ['a', ])
        self.assertEquals(this_is_a_thing.cache_keys_excluded, [])
        self.assertEquals(this_is_a_thing.cache_keys, ['a', ])

    def test_exclude(self):
        @cache(exclude=['a', ])
        def this_is_a_thing(a, b, c):
            return a + b + c

        self.assertEquals(this_is_a_thing.cache_keys_included, [])
        self.assertEquals(this_is_a_thing.cache_keys_excluded, ['a', ])
        self.assertEquals(this_is_a_thing.cache_keys, ['b', 'c'])

    def test_exclude_non_existing_field(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            @cache(exclude=['e', ])
            def this_is_a_thing(a, b, c):
                return a + b + c
        self.assertEquals(str(e.exception), 'Invalid key on exclude: "e". Keys allowed to be excluded: "a", "b", "c"')

    def test_exclude_malformed(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            @cache(exclude=['a.in.depth', ])
            def this_is_a_thing(a, b, c):
                return a + b + c
        self.assertEquals(str(e.exception), 'Invalid key on exclude: "a.in.depth". Keys allowed to be excluded: "a", "b", "c"')
