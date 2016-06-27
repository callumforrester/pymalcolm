import os
import sys
from collections import OrderedDict
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import setup_malcolm_paths
import unittest

from malcolm.core.stringarraymeta import StringArrayMeta
from malcolm.core.attributemeta import AttributeMeta

class TestStringArrayMeta(unittest.TestCase):

    def setUp(self):
        self.meta = StringArrayMeta("test_meta", "test description")

    def test_init(self):
        self.assertEqual("test_meta", self.meta.name)
        self.assertEqual("test description", self.meta.description)
        self.assertEqual(self.meta.metaOf, "malcolm:core/StringArray:1.0")

    def test_validate_none(self):
        self.assertIsNone(self.meta.validate(None))

    def test_validate_array(self):
        array = ["test_string", 123, 123.456]
        self.assertEquals(
            ["test_string", "123", "123.456"],
            self.meta.validate(array))

    def test_not_iterable_raises(self):
        value = 12346
        self.assertRaises(ValueError, self.meta.validate, value)

    def test_null_element_raises(self):
        array = ["test", None]
        self.assertRaises(ValueError, self.meta.validate, array)

    def test_to_dict(self):
        expected = OrderedDict()
        expected["description"] = "test description"
        expected["metaOf"] = "malcolm:core/StringArray:1.0"
        self.assertEqual(expected, self.meta.to_dict())

    def test_from_dict(self):
        d = OrderedDict()
        d["description"] = "test array description"
        d["metaOf"]= "malcolm:core/StringArray:1.0"
        s = AttributeMeta.from_dict("test_array_meta", d)
        self.assertEqual(StringArrayMeta, type(s))
        self.assertEqual(s.name, "test_array_meta")
        self.assertEqual(s.description, "test array description")
        self.assertEqual(d, s.to_dict())


if __name__ == "__main__":
    unittest.main()
