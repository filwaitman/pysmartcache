# -*- coding: utf-8 -*-

import datetime
import os
import unittest

from freezegun import freeze_time
import mock

from pysmartcache.clients import CacheClient
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
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

    def test_missed_outdated(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

        with freeze_time(self.now + datetime.timedelta(seconds=60)):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 1)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

    def test_missed_missed(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

    def test_sequence(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 2)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 3)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 3)
            self.assertEqual(self.cache_outdated_patched.call_count, 1)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 4)
            self.assertEqual(self.cache_outdated_patched.call_count, 1)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 4)
            self.assertEqual(self.cache_outdated_patched.call_count, 2)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

    def test_cache_purge(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            CacheClient.instantiate(self.cache_backend).purge()

            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 3)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 4)

    def test_cache_invalidate(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            kinda_sum.cache_invalidate_for(2, 4)

            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 3)

    def test_cache_info(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

        with freeze_time(self.now + datetime.timedelta(seconds=3)):
            info = kinda_sum.cache_info_for(2, 3)
            self.assertEqual(info['value'], 5)
            self.assertEqual(info['date added'], self.now)
            self.assertEqual(info['outdated'], False)
            self.assertEqual(info['timeout'], 10)
            self.assertEqual(info['age'], 3)

        with freeze_time(self.now + datetime.timedelta(seconds=13)):
            info = kinda_sum.cache_info_for(2, 3)
            self.assertEqual(info['value'], 5)
            self.assertEqual(info['date added'], self.now)
            self.assertEqual(info['outdated'], True)
            self.assertEqual(info['timeout'], 10)
            self.assertEqual(info['age'], 13)

    def test_cache_refresh(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)
            self.assertEqual(kinda_sum.cache_info_for(2, 3)['date added'], self.now)

        with freeze_time(self.now + datetime.timedelta(seconds=5)):
            result = kinda_sum.cache_refresh_for(2, 3)

            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)
            self.assertEqual(kinda_sum.cache_info_for(2, 3)['date added'], self.now + datetime.timedelta(seconds=5))

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)
            self.assertEqual(kinda_sum.cache_info_for(2, 3)['date added'], self.now + datetime.timedelta(seconds=5))

    def test_only_declared_keys_matter_for_cache_sake(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=None)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 2)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=42)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 3)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=True)
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 4)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

    def test_methods_decorated_inside_classes_work_exactly_the_same_way(self):
        with freeze_time(self.now):
            result = KindaSumClass(2, 3).just_do_it()
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = KindaSumClass(2, 3).just_do_it()
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 2)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 3)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = KindaSumClass(2, 3).just_do_it()
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 3)
            self.assertEqual(self.cache_outdated_patched.call_count, 1)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 3).just_do_it()
            self.assertEqual(result, 5)
            self.assertEqual(self.cache_hit_patched.call_count, 4)
            self.assertEqual(self.cache_outdated_patched.call_count, 1)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEqual(result, 6)
            self.assertEqual(self.cache_hit_patched.call_count, 4)
            self.assertEqual(self.cache_outdated_patched.call_count, 2)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

    def test_deep_attribute_changed_on_keys_affect_cache(self):
        with freeze_time(self.now):
            child = AnotherClass(a=2, b=10)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEqual(result, 7)

            self.assertEqual(self.cache_hit_patched.call_count, 0)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            child = AnotherClass(a=2, b=10)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEqual(result, 7)

            self.assertEqual(self.cache_hit_patched.call_count, 1)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            child = AnotherClass(a=2, b=10000)  # b doesn't matter for this cache
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEqual(result, 7)

            self.assertEqual(self.cache_hit_patched.call_count, 2)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 1)

            child = AnotherClass(a=37, b=10000)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEqual(result, 42)

            self.assertEqual(self.cache_hit_patched.call_count, 2)
            self.assertEqual(self.cache_outdated_patched.call_count, 0)
            self.assertEqual(self.cache_missed_patched.call_count, 2)

    def test_raise_exception_properly(self):
        @cache(['a', 'b'], timeout=CACHE_TIMEOUT, verbose=CACHE_VERBOSE)
        def kinda_sum_broken(a, b, useless_parameter_for_cache=None):
            return a + b / 0

        @cache(['a', 'b'], timeout=CACHE_TIMEOUT, verbose=CACHE_VERBOSE)
        def kinda_sum_broken2(a, b, useless_parameter_for_cache=None):
            return a + b.wild_attr

        with self.assertRaises(ZeroDivisionError) as e:
            kinda_sum_broken(2, 3)
        self.assertTrue(str(e.exception).endswith('by zero'))

        with self.assertRaises(AttributeError) as e:
            kinda_sum_broken2(2, 3)
        self.assertTrue(str(e.exception).endswith("has no attribute 'wild_attr'"))


class MemcachedClientEngineTestCase(CacheCommonTestCase, unittest.TestCase):
    cache_backend = 'memcached'


class RedisClientEngineTestCase(CacheCommonTestCase, unittest.TestCase):
    cache_backend = 'redis'


class CacheKeysTestCase(unittest.TestCase):
    def test_neither_include_nor_exclude(self):
        @cache()
        def this_is_a_thing(a, b, c):
            return a + b + c

        self.assertEqual(this_is_a_thing.cache_keys_included, [])
        self.assertEqual(this_is_a_thing.cache_keys_excluded, [])
        self.assertEqual(this_is_a_thing.cache_keys, ['a', 'b', 'c'])

    def test_both_include_and_exclude(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            @cache(include=['a', ], exclude=['a', ])
            def this_is_a_thing(a, b, c):
                return a + b + c
        self.assertEqual(str(e.exception), 'You shall not provide both include and exclude arguments')

    def test_include(self):
        @cache(include=['a', ])
        def this_is_a_thing(a, b, c):
            return a + b + c

        self.assertEqual(this_is_a_thing.cache_keys_included, ['a', ])
        self.assertEqual(this_is_a_thing.cache_keys_excluded, [])
        self.assertEqual(this_is_a_thing.cache_keys, ['a', ])

    def test_exclude(self):
        @cache(exclude=['a', ])
        def this_is_a_thing(a, b, c):
            return a + b + c

        self.assertEqual(this_is_a_thing.cache_keys_included, [])
        self.assertEqual(this_is_a_thing.cache_keys_excluded, ['a', ])
        self.assertEqual(this_is_a_thing.cache_keys, ['b', 'c'])

    def test_exclude_non_existing_field(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            @cache(exclude=['e', ])
            def this_is_a_thing(a, b, c):
                return a + b + c
        self.assertEqual(str(e.exception), 'Invalid key on exclude: "e". Keys allowed to be excluded: "a", "b", "c"')

    def test_exclude_malformed(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            @cache(exclude=['a.in.depth', ])
            def this_is_a_thing(a, b, c):
                return a + b + c
        self.assertEqual(str(e.exception), 'Invalid key on exclude: "a.in.depth". Keys allowed to be excluded: "a", "b", "c"')
