# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal
import unittest

from pysmartcache.exceptions import InvalidTypeForUniqueRepresentation, UniqueRepresentationNotFound
from pysmartcache.object_representations import UniqueRepresentation, get_unique_representation


class GetUniqueRepresentationTestCase(unittest.TestCase):
    def test_object_with_explicit_cache_key_method(self):
        class Sloth(object):
            lazy = 2

            def __cache_key__(self):
                return str(self.lazy * 2)

        sloth = Sloth()
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.4')

        sloth.lazy = 10
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.20')

    def test_object_with_uuid_attribute(self):
        class Sloth(object):
            uuid = '123'

        sloth = Sloth()
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.123')

        sloth.uuid = '456'
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.456')

    def test_object_with_id_attribute(self):
        class Sloth(object):
            id = '1'

        sloth = Sloth()
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.1')

        sloth.id = '2'
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.2')

    def test_datetime_derivate_object(self):
        self.assertEqual(get_unique_representation(datetime.datetime(2015, 1, 2, 3, 4, 5)), '2015-01-02T03:04:05')
        self.assertEqual(get_unique_representation(datetime.date(2015, 1, 2)), '2015-01-02')
        self.assertEqual(get_unique_representation(datetime.time(3, 4, 5)), '03:04:05')

    def test_decimal(self):
        self.assertEqual(get_unique_representation(Decimal(1.618033989)), '1.618033989')

    def test_None(self):
        self.assertEqual(get_unique_representation(None), repr(None))

    def test_primitive_objects(self):
        self.assertEqual(get_unique_representation(1), repr(1))
        self.assertEqual(get_unique_representation('sloth'), repr('sloth'))
        self.assertEqual(get_unique_representation(False), repr(False))
        self.assertEqual(get_unique_representation(3.14159), repr(3.14159))

    def test_dicts(self):
        gur = get_unique_representation
        self.assertEqual(gur({}), '')
        self.assertEqual(gur({'key1': 'value1'}), '--'.join([gur('key1'), gur('value1')]))
        self.assertEqual(gur({False: [1, 2, 3]}), '--'.join([gur(False), '--'.join([gur(1), gur(2), gur(3)])]))
        self.assertEqual(
            gur({False: {'depth': {2: True}}}),
            '--'.join(
                [gur(False), '--'.join(
                    [gur('depth'), '--'.join(
                        [gur(2),
                         gur(True)]
                    )]
                )]
            )
        )

    def test_iterables_other_than_dicts(self):
        gur = get_unique_representation
        self.assertEqual(gur([]), '')
        self.assertEqual(gur([1, 2, 'str']), '--'.join([gur(1), gur(2), gur('str')]))
        self.assertEqual(
            gur([1, 2, (3, {4, }, False), 5]),
            '--'.join(
                [gur(1), gur(2), '--'.join(
                    [gur(3), '--'.join(
                        [gur(4)]),
                        gur(False)]),
                    gur(5)])
        )

    def test_instance_fallback_order(self):
        class Sloth(object):
            def __init__(self):
                self.id = 'id'
                self.uuid = 'uuid'
                self.__cache_key__ = lambda: 'cache_key'

        sloth = Sloth()
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.cache_key')

        del sloth.__cache_key__
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.uuid')

        del sloth.uuid
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.id')

        del sloth.id
        with self.assertRaises(UniqueRepresentationNotFound) as e:
            get_unique_representation(sloth)
        self.assertTrue(str(e.exception).endswith('has not declared an unique representation'))

    def test_max_lenght(self):
        # we strive to keep cache_key as a kind of readable thing.
        # However, when key is too long we need to shorten that - in order to avoid memcached key lenght restrictions.
        self.assertEqual(len(get_unique_representation(list(range(200)))), 32)

    def test_custom_representation(self):
        class SlothRepresented(object):
            pass

        class SlothUniqueRepresentation(UniqueRepresentation):
            def get_unique_representation(self, obj):
                if isinstance(obj, SlothRepresented):
                    return 'custom-representation-for-sloth'

        sloth = SlothRepresented()
        self.assertEqual(get_unique_representation(sloth), 'custom-representation-for-sloth')

    def test_custom_representation_not_returning_string(self):
        class SlothBadlyRepresented(object):
            pass

        class SlothUniqueRepresentation(UniqueRepresentation):
            def get_unique_representation(self, obj):
                if isinstance(obj, SlothBadlyRepresented):
                    return 42

        sloth = SlothBadlyRepresented()
        with self.assertRaises(InvalidTypeForUniqueRepresentation) as e:
            get_unique_representation(sloth)
        self.assertTrue(str(e.exception).endswith('instance: 42'))

    def test_object_without_unique_representation(self):
        class Sloth(object):
            pass

        sloth = Sloth()
        with self.assertRaises(UniqueRepresentationNotFound) as e:
            get_unique_representation(sloth)
        self.assertTrue(str(e.exception).endswith('has not declared an unique representation'))

    def test_object_with_cache_key_declared_returning_something_different_to_string(self):
        class Sloth(object):
            def __init__(self):
                self.__cache_key__ = lambda: 'cache_key'

        sloth = Sloth()
        self.assertEqual(get_unique_representation(sloth), 'tests.test_object_representations.Sloth.cache_key')

        sloth.__cache_key__ = lambda: False
        with self.assertRaises(InvalidTypeForUniqueRepresentation) as e:
            get_unique_representation(sloth)
        self.assertEqual(str(e.exception), 'obj.__cache_key__() must return a string')

        sloth.__cache_key__ = lambda: 42
        with self.assertRaises(InvalidTypeForUniqueRepresentation) as e:
            get_unique_representation(sloth)
        self.assertEqual(str(e.exception), 'obj.__cache_key__() must return a string')

        sloth.__cache_key__ = lambda: None
        with self.assertRaises(InvalidTypeForUniqueRepresentation) as e:
            get_unique_representation(sloth)
        self.assertEqual(str(e.exception), 'obj.__cache_key__() must return a string')
