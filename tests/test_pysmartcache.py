# -*- coding: utf-8 -*-
from collections import namedtuple
import datetime
from decimal import Decimal
import os
import unittest

from freezegun import freeze_time
import mock

from pysmartcache import CacheEngine, cache, depth_getattr, get_unique_representation

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


class CacheCommonTestCase(unittest.TestCase):
    def setUp(self):
        super(CacheCommonTestCase, self).setUp()
        CacheEngine.purge()
        self.now = datetime.datetime.utcnow()

        self._patch1 = mock.patch.object(CacheEngine, '_cache_hit_signal')
        self.cache_hit_patched = self._patch1.start()
        self._patch2 = mock.patch.object(CacheEngine, '_cache_outdated_signal')
        self.cache_outdated_patched = self._patch2.start()
        self._patch3 = mock.patch.object(CacheEngine, '_cache_miss_signal')
        self.cache_miss_patched = self._patch3.start()
        self.mocks = [self._patch1, self._patch2, self._patch3]

    def tearDown(self):
        super(CacheCommonTestCase, self).tearDown()
        for mock_ in self.mocks:
            mock_.stop()

    def test_miss_hit(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

    def test_miss_outdated(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

        with freeze_time(self.now + datetime.timedelta(seconds=60)):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

    def test_miss_miss(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

    def test_sequence(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 2)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

    def test_cache_purge(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            CacheEngine.purge()

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 3)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 4)

    def test_cache_invalidate(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            kinda_sum.cache_invalidate_for(2, 4)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = kinda_sum(2, 4)
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 3)

    def test_cache_info(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

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
            self.assertEquals(self.cache_miss_patched.call_count, 1)
            self.assertEquals(kinda_sum.cache_info_for(2, 3)['date added'], self.now)

        with freeze_time(self.now + datetime.timedelta(seconds=5)):
            result = kinda_sum.cache_refresh_for(2, 3)

            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)
            self.assertEquals(kinda_sum.cache_info_for(2, 3)['date added'], self.now + datetime.timedelta(seconds=5))

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)
            self.assertEquals(kinda_sum.cache_info_for(2, 3)['date added'], self.now + datetime.timedelta(seconds=5))

    def test_only_declared_keys_matter_for_cache_sake(self):
        with freeze_time(self.now):
            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 3)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=None)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=42)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = kinda_sum(2, 3, useless_parameter_for_cache=True)
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

    def test_methods_decorated_inside_classes_work_exactly_the_same_way(self):
        with freeze_time(self.now):
            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

        with freeze_time(self.now + datetime.timedelta(seconds=11)):
            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 3)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = KindaSumClass(2, 3).just_do_it()
            self.assertEquals(result, 5)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 1)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

            result = KindaSumClass(2, 4).just_do_it()
            self.assertEquals(result, 6)
            self.assertEquals(self.cache_hit_patched.call_count, 4)
            self.assertEquals(self.cache_outdated_patched.call_count, 2)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

    def test_deep_attribute_changed_on_keys_affect_cache(self):
        with freeze_time(self.now):
            child = AnotherClass(a=2, b=10)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 7)

            self.assertEquals(self.cache_hit_patched.call_count, 0)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            child = AnotherClass(a=2, b=10)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 7)

            self.assertEquals(self.cache_hit_patched.call_count, 1)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            child = AnotherClass(a=2, b=10000)  # b doesn't matter for this cache
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 7)

            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 1)

            child = AnotherClass(a=37, b=10000)
            result = KindaSumClass(2, 3, child=child).depending_on_child()
            self.assertEquals(result, 42)

            self.assertEquals(self.cache_hit_patched.call_count, 2)
            self.assertEquals(self.cache_outdated_patched.call_count, 0)
            self.assertEquals(self.cache_miss_patched.call_count, 2)

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


class DepthGetattrHelperTestCase(unittest.TestCase):
    def test_common(self):
        something = 42
        some_class = namedtuple('some_class', ['child'])
        class1 = some_class(something)
        class2 = some_class(class1)

        self.assertEquals(depth_getattr(something, ''), something)
        self.assertEquals(depth_getattr(something, 'imag'), something.imag)

        self.assertEquals(depth_getattr(class1, ''), class1)
        self.assertEquals(depth_getattr(class1, 'child'), something)
        self.assertEquals(depth_getattr(class1, 'child.imag'), something.imag)

        self.assertEquals(depth_getattr(class2, ''), class2)
        self.assertEquals(depth_getattr(class2, 'child'), class1)
        self.assertEquals(depth_getattr(class2, 'child.child'), something)
        self.assertEquals(depth_getattr(class2, 'child.child.imag'), something.imag)

    def test_raise_exception_properly(self):
        something = 42
        with self.assertRaises(AttributeError) as e:
            depth_getattr(something, 'boom')
        self.assertEquals(str(e.exception), "'int' object has no attribute 'boom'")


class GetUniqueRepresentationHelperTestCase(unittest.TestCase):
    def test_object_with_explicit_cache_key_method(self):
        class Sloth(object):
            lazy = 2

            def __cache_key__(self):
                return self.lazy * 2

        sloth = Sloth()
        self.assertEquals(get_unique_representation(sloth), repr(4))

        sloth.lazy = 10
        self.assertEquals(get_unique_representation(sloth), repr(20))

    def test_object_with_uuid_attribute(self):
        class Sloth(object):
            uuid = '123'

        sloth = Sloth()
        self.assertEquals(get_unique_representation(sloth), repr('123'))

        sloth.uuid = '456'
        self.assertEquals(get_unique_representation(sloth), repr('456'))

    def test_object_with_id_attribute(self):
        class Sloth(object):
            id = '1'

        sloth = Sloth()
        self.assertEquals(get_unique_representation(sloth), repr('1'))

        sloth.id = '2'
        self.assertEquals(get_unique_representation(sloth), repr('2'))

    def test_datetime_derivate_object(self):
        self.assertEquals(get_unique_representation(datetime.datetime(2015, 1, 2, 3, 4, 5)), repr('2015-01-02T03:04:05'))
        self.assertEquals(get_unique_representation(datetime.date(2015, 1, 2)), repr('2015-01-02'))
        self.assertEquals(get_unique_representation(datetime.time(3, 4, 5)), repr('03:04:05'))

    def test_decimal(self):
        self.assertEquals(get_unique_representation(round(Decimal(1.618033989), 9)), repr(1.618033989))

    def test_None(self):
        self.assertEquals(get_unique_representation(None), repr(None))

    def test_primitive_objects(self):
        self.assertEquals(get_unique_representation(1), repr(1))
        self.assertEquals(get_unique_representation('sloth'), repr('sloth'))
        self.assertEquals(get_unique_representation(False), repr(False))
        self.assertEquals(get_unique_representation(3.14159), repr(3.14159))

    def test_dicts(self):
        gur = get_unique_representation
        self.assertEquals(gur({}), repr(''))
        self.assertEquals(gur({'key1': 'value1'}), repr('--'.join([gur('key1'), gur('value1')])))
        self.assertEquals(gur({False: [1, 2, 3]}), repr('--'.join([gur(False), repr('--'.join([gur(1), gur(2), gur(3)]))])))
        self.assertEquals(
            gur({False: {'depth': {2: True}}}),
            repr(
                '--'.join([gur(False),
                repr(
                    '--'.join([gur('depth'),
                    repr(
                        '--'.join([gur(2), gur(True)]))
                    ]))
                ]))
        )

    def test_iterables_other_than_dicts(self):
        gur = get_unique_representation
        self.assertEquals(gur([]), repr(''))
        self.assertEquals(gur([1, 2, 'str']), repr('--'.join([gur(1), gur(2), gur('str')])))
        self.assertEquals(
            gur([1, 2, (3, {4, }, False), 5]),
            repr(
                '--'.join([gur(1), gur(2),
                repr(
                    '--'.join([gur(3),
                    repr(
                        '--'.join([gur(4)])),
                    gur(False)])),
                gur(5)]))
        )

    def test_instance_fallback_order(self):
        class Sloth(object):
            def __init__(self):
                self.id = 'id'
                self.uuid = 'uuid'
                self.__cache_key__ = lambda: 'cache_key'

        sloth = Sloth()
        self.assertEquals(get_unique_representation(sloth), repr('cache_key'))

        del sloth.__cache_key__
        self.assertEquals(get_unique_representation(sloth), repr('uuid'))

        del sloth.uuid
        self.assertEquals(get_unique_representation(sloth), repr('id'))

    def test_max_lenght(self):
        # we strive to keep cache_key as a kind of readable thing.
        # However, when key is too long we need to shorten that - in order to avoid memcached key lenght restrictions.
        self.assertEquals(len(get_unique_representation(range(200))), 32)


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
        os.environ.pop('PYSMARTCACHE_HOSTS', None)
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

        with self.assertRaises(RuntimeError) as e:
            os.environ['PYSMARTCACHE_TIMEOUT'] = 'NaN'
            CacheEngine._get_timeout(None)
        self.assertEquals(str(e.exception), 'PYSMARTCACHE_TIMEOUT OS var must be numeric')

        with self.assertRaises(RuntimeError) as e:
            CacheEngine._get_timeout(-42)
        self.assertEquals(str(e.exception), 'Timeout must be positive')

        with self.assertRaises(RuntimeError) as e:
            CacheEngine._get_timeout(0)
        self.assertEquals(str(e.exception), 'Timeout must be positive')

    def test_low_level_hosts(self):
        self.assertEquals(CacheEngine._get_hosts(None), CacheEngine.DEFAULT_HOSTS)
        self.assertEquals(CacheEngine._get_hosts(['192.168.0.1:11212', ]), ['192.168.0.1:11212', ])

        os.environ['PYSMARTCACHE_HOSTS'] = '192.168.0.1:11212,192.168.0.1:11213'
        self.assertEquals(CacheEngine._get_hosts(None), ['192.168.0.1:11212', '192.168.0.1:11213'])
        self.assertEquals(CacheEngine._get_hosts(['192.168.0.1:11212', ]), ['192.168.0.1:11212', ])

        with self.assertRaises(RuntimeError) as e:
            CacheEngine._get_hosts([])
        self.assertEquals(str(e.exception), 'Hosts can not be empty')

    def test_low_level_verbose(self):
        self.assertEquals(CacheEngine._get_verbose(None), CacheEngine.DEFAULT_VERBOSE)
        self.assertEquals(CacheEngine._get_verbose(True), True)

        os.environ['PYSMARTCACHE_VERBOSE'] = '1'
        self.assertEquals(CacheEngine._get_verbose(None), True)

        os.environ['PYSMARTCACHE_VERBOSE'] = '0'
        self.assertEquals(CacheEngine._get_verbose(None), False)
        self.assertEquals(CacheEngine._get_verbose(True), True)

        with self.assertRaises(RuntimeError) as e:
            os.environ['PYSMARTCACHE_VERBOSE'] = 'NaN'
            CacheEngine._get_verbose(None)
        self.assertEquals(str(e.exception), 'PYSMARTCACHE_VERBOSE OS var must be numeric')

        with self.assertRaises(RuntimeError) as e:
            os.environ['PYSMARTCACHE_VERBOSE'] = '42'
            CacheEngine._get_verbose(None)
        self.assertEquals(str(e.exception), 'PYSMARTCACHE_VERBOSE OS var must be 0 or 1')
