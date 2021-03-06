import unittest
from collections import OrderedDict

from malcolm.modules.builtin.vmetas import NumberMeta


class TestInit(unittest.TestCase):
    def test_init(self):
        nm = NumberMeta("float32")
        assert nm.typeid == "malcolm:core/NumberMeta:1.0"
        assert nm.dtype == "float32"
        assert nm.label == ""


class TestValidate(unittest.TestCase):

    def test_float_against_float32(self):
        nm = NumberMeta("float32")
        self.assertAlmostEqual(123.456, nm.validate(123.456), places=5)

    def test_float_against_float64(self):
        nm = NumberMeta("float64")
        assert 123.456 == nm.validate(123.456)

    def test_int_against_float(self):
        nm = NumberMeta("float64")
        assert 123 == nm.validate(123)

    def test_int_against_int(self):
        nm = NumberMeta("int32")
        assert 123 == nm.validate(123)

    def test_float_to_int_truncates(self):
        nm = NumberMeta("int32")
        assert nm.validate(123.6) == 123

    def test_none_validates(self):
        nm = NumberMeta("int32")
        assert 0 == nm.validate(None)

    def test_unsigned_validates(self):
        nm = NumberMeta("uint32")
        assert nm.validate("22") == 22
        assert nm.validate(-22) == 2**32-22


class TestSerialization(unittest.TestCase):

    def setUp(self):
        self.serialized = OrderedDict()
        self.serialized["typeid"] = "malcolm:core/NumberMeta:1.0"
        self.serialized["dtype"] = "float64"
        self.serialized["description"] = "desc"
        self.serialized["tags"] = ()
        self.serialized["writeable"] = False
        self.serialized["label"] = "name"

    def test_to_dict(self):
        nm = NumberMeta("float64", "desc", label="name")
        assert nm.to_dict() == self.serialized

    def test_from_dict(self):
        nm = NumberMeta.from_dict(self.serialized)
        assert type(nm) == NumberMeta
        assert nm.description == "desc"
        assert nm.dtype == "float64"
        assert nm.tags == ()
        assert not nm.writeable
        assert nm.label == "name"
