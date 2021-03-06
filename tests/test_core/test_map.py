import unittest
from collections import OrderedDict
from mock import MagicMock, Mock

from malcolm.core import Map
from malcolm.modules.builtin.vmetas import NumberMeta, StringMeta
from malcolm.core.meta import Meta
from malcolm.core.mapmeta import MapMeta


class TestMap(unittest.TestCase):

    def setUp(self):
        n = NumberMeta(description='a number')
        s = StringMeta(description="a string")
        self.meta = MapMeta()
        self.meta.set_elements({"a": s, "b": s})
        self.meta.set_required(["a"])
        self.nmeta = MapMeta()
        self.nmeta.set_elements({"a": n, "b": n})
        self.nmeta.set_required(["a"])

    def test_init(self):
        b_mock = MagicMock()
        m = Map(self.meta, {"a":"test", "b":b_mock})
        assert self.meta == m.meta
        assert "test" == m.a
        self.assertIs(str(b_mock), m.b)
        assert "malcolm:core/Map:1.0" == m.typeid

    def test_init_raises_on_bad_key(self):
        with self.assertRaises(ValueError):
            m = Map(self.meta, {"bad_key":MagicMock()})

    def test_empty_init(self):
        m = Map(self.meta, None)
        assert self.meta == m.meta
        with self.assertRaises(AttributeError):
            m.a

    def test_to_dict(self):
        s = StringMeta(description="a string")
        meta = MapMeta()
        elements = OrderedDict()
        elements["b"] = s
        elements["c"] = s
        elements["d"] = NumberMeta("int32")
        elements["e"] = s
        meta.set_elements(elements)
        m = Map(meta, {"b": "test", "d": 123, "e": "e"})

        expected = OrderedDict()
        expected["typeid"] = "malcolm:core/Map:1.0"
        expected["b"] = "test"
        expected["d"] = 123
        expected["e"] = "e"
        assert expected == m.to_dict()

    def test_from_dict(self):
        map_meta = MagicMock()
        map_meta.elements = {"a": Mock(), "b": Mock(), "c": Mock()}
        map_meta.elements["a"].validate.return_value = 124
        map_meta.elements["b"].validate.return_value = "Something"
        map_meta.required = ["a"]

        d = {"a":123, "b":{"typeid":"mock_typeid"}}
        m = Map(map_meta, d)
        assert 124 == m.a
        assert "Something" == m.b

    def test_equals_maps(self):
        self.meta.to_dict = MagicMock()
        m1 = Map(self.meta, {"a":"test"})
        m2 = Map(self.meta, {"a":"test2"})
        assert not m1 == m2
        assert m1 != m2
        m2.a = "test"
        assert m1 == m2
        assert not m1 != m2

        m2 = Map(self.meta, {"a":"test", "b":"test"})
        assert not m1 == m2
        m1["b"] = "test"
        assert m1 == m2

        s = StringMeta(description="a string")
        meta2 = Meta()
        meta2.elements = {"a":s, "b":s}
        meta2.required = ["a"]
        meta2.to_dict = self.meta.to_dict
        m2 = Map(meta2, {"a":"test", "b":"test"})
        assert m1 == m2

    def test_equals_dicts(self):
        m = Map(self.meta, {"a":"test"})
        d = {"a":"test"}
        assert m == d
        assert not m != d

        m["b"] = "test"
        assert not m == d
        assert m != d

        d["b"] = "test2"
        assert not m == d
        assert m != d

        d["b"] = "test"
        assert m == d
        assert not m != d

    def test_contains(self):
        m = Map(self.meta, {"a":"test"})
        assert "a" in m
        assert not "b" in m
        assert not "__init__" in m

    def test_get_item(self):
        m = Map(self.meta, {"a":"test"})
        assert "test" == m["a"]
        m.a = "test_2"
        assert "test_2" == m["a"]

    def test_get_item_raises_if_no_key(self):
        m = Map(self.meta, {"a":"test"})
        with self.assertRaises(KeyError):
            m["b"]

    def test_get_item_fails_if_non_key(self):
        m = Map(self.meta)
        with self.assertRaises(KeyError):
            m["__init__"]

    def test_set_item(self):
        m = Map(self.meta, {"a":1})
        a_mock = MagicMock()
        b_mock = MagicMock()
        m["a"] = a_mock
        m["b"] = b_mock
        assert str(a_mock) == m.a
        assert str(b_mock) == m.b

    def test_set_item_raises_invalid_key(self):
        m = Map(self.meta)
        with self.assertRaises(ValueError):
            m["c"] = MagicMock()

    def test_len(self):
        m = Map(self.meta)
        assert 0 == len(m)
        m.a = 1
        assert 1 == len(m)
        m.b = 1
        assert 2 == len(m)

    def test_iter(self):
        m = Map(self.meta, {"a":"x", "b":"y"})
        assert {"a", "b"} == {x for x in m}

    def test_update(self):
        m = Map(self.nmeta, {"a":1})
        d = {"a":2, "b":2}
        m.update(d)
        assert 2 == m.a
        assert 2 == m.b

    def test_update_raises_on_invalid_key(self):
        m = Map(self.nmeta, {"a":1})
        d = {"a":2, "b":2, "c":2}
        with self.assertRaises(ValueError):
            m.update(d)
        assert 1 == m.a
        with self.assertRaises(AttributeError):
            m.b
        with self.assertRaises(AttributeError):
            m.c

    def test_clear(self):
        m = Map(self.nmeta, {"a":1})
        m.clear()
        with self.assertRaises(AttributeError):
            m.a

    def test_keys(self):
        m = Map(self.nmeta, {"a": 1})
        assert ["a"] == list(m.keys())
        m.b = 1
        assert {"a", "b"} == set(m.keys())

    def test_values(self):
        m = Map(self.nmeta, {"a":1})
        assert [1] == list(m.values())
        m.b = 2
        assert {1, 2} == set(m.values())

    def test_items(self):
        m = Map(self.nmeta, {"b":2})
        assert [("b", 2)] == list(m.items())
        m.a = 1
        assert {("a", 1), ("b", 2)} == set(m.items())

    def test_repr(self):
        m = Map(self.nmeta, {"b": 44})
        r = repr(m)
        assert r == "Map({'b': 44.0})"
