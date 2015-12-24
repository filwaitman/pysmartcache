# -*- coding: utf-8 -*-
from collections import namedtuple
import unittest

from pysmartcache.utils import depth_getattr


class DepthGetattrTestCase(unittest.TestCase):
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
