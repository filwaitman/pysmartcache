# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import, print_function
from collections import namedtuple
from decimal import Decimal
import unittest

import mock

from pysmartcache.exceptions import ImproperlyConfigured
from pysmartcache.utils import uid, depth_getattr, get_env_var  # , get_cache_key


class Fixture1(object):
    x = 'x'
    y = 'y'

    def __init__(self, x='x', y='y'):
        self.x = x
        self.y = y


class Fixture2(object):
    x = 'x'
    y = 'y'

    def __init__(self, x='x', y='y'):
        self.x = x
        self.y = y


class UidTestCase(unittest.TestCase):
    def test_common(self):
        uid1 = uid('xxxx')
        self.assertEqual(uid('xxxx'), uid1)
        self.assertNotEqual(uid('xxx'), uid1)
        self.assertNotEqual(uid('xxxxx'), uid1)
        self.assertNotEqual(uid('XXX'), uid1)

        uid2 = uid('42')
        self.assertEqual(uid('42'), uid2)
        self.assertNotEqual(uid(42), uid2)
        self.assertNotEqual(uid(42.0), uid2)
        self.assertNotEqual(uid(Decimal('42.0')), uid2)

        uid3 = uid(Fixture1)
        self.assertEqual(uid(Fixture1), uid3)
        self.assertNotEqual(uid(Fixture1()), uid3)
        self.assertNotEqual(uid(Fixture2), uid3)
        self.assertNotEqual(uid(Fixture2()), uid3)

        uid4 = uid(Fixture1(x='x', y='y'))
        self.assertEqual(uid(Fixture1(x='x', y='y')), uid4)
        self.assertEqual(uid(Fixture1()), uid4)
        self.assertNotEqual(uid(Fixture1(x='X', y='YY')), uid4)
        self.assertNotEqual(uid(Fixture2(x='x', y='y')), uid4)
        self.assertNotEqual(uid(Fixture2()), uid4)


class DepthGetattrTestCase(unittest.TestCase):
    def test_common(self):
        something = 42
        some_class = namedtuple('some_class', ['child'])
        class1 = some_class(something)
        class2 = some_class(class1)

        self.assertEqual(depth_getattr(something, ''), something)
        self.assertEqual(depth_getattr(something, 'imag'), something.imag)

        self.assertEqual(depth_getattr(class1, ''), class1)
        self.assertEqual(depth_getattr(class1, 'child'), something)
        self.assertEqual(depth_getattr(class1, 'child.imag'), something.imag)

        self.assertEqual(depth_getattr(class2, ''), class2)
        self.assertEqual(depth_getattr(class2, 'child'), class1)
        self.assertEqual(depth_getattr(class2, 'child.child'), something)
        self.assertEqual(depth_getattr(class2, 'child.child.imag'), something.imag)

    def test_raise_exception_properly(self):
        something = 42
        with self.assertRaises(AttributeError) as e:
            depth_getattr(something, 'boom')
        self.assertEqual(str(e.exception), "'int' object has no attribute 'boom'")


@mock.patch('pysmartcache.utils.os')
class GetEnvVarTestCase(unittest.TestCase):
    def test_bool_positive_values(self, os_patched):
        os_patched.environ.get.return_value = 'True'
        self.assertTrue(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = '1'
        self.assertTrue(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = 't'
        self.assertTrue(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = 'y'
        self.assertTrue(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = 'yes'
        self.assertTrue(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

    def test_bool_negative_values(self, os_patched):
        os_patched.environ.get.return_value = 'False'
        self.assertFalse(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = '0'
        self.assertFalse(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = 'f'
        self.assertFalse(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = 'n'
        self.assertFalse(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

        os_patched.environ.get.return_value = 'no'
        self.assertFalse(get_env_var('WHATEVER (IT IS MOCKED)', cast=bool))

    def test_invalid_values(self, os_patched):
        os_patched.environ.get.return_value = 'Hamster'
        self.assertEquals(get_env_var('WHATEVER (IT IS MOCKED)'), 'Hamster')  # No casting so that's ok.

        self.assertRaises(ImproperlyConfigured, get_env_var, 'WHATEVER (IT IS MOCKED)', cast=bool)
        self.assertRaises(ImproperlyConfigured, get_env_var, 'WHATEVER (IT IS MOCKED)', cast=int)

    def test_defaults(self, os_patched):
        os_patched.environ.get.return_value = None
        self.assertEquals(get_env_var('WHATEVER (IT IS MOCKED)'), None)
        self.assertEquals(get_env_var('WHATEVER (IT IS MOCKED)', cast=int), None)
        self.assertEquals(get_env_var('WHATEVER (IT IS MOCKED)', cast=int, default=2), 2)
