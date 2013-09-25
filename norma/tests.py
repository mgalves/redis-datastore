#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import redis
import unittest

import structs

class TestDict(unittest.TestCase):

    def setUp(self):
        self.redis = redis.Redis()
        self.redis.flushdb()

    def test_empty_dict(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.Dict()
        self.assertEqual(len(d), 0)
        self.assertEqual(d.keys(), [])
        self.assertEqual(d.values(), [])
        self.assertEqual(d.items(), [])

    def test_dict_default_id(self):
        d = structs.Dict()
        d["1"] = 2
        self.assertEqual(d.pk, id(d))
        keys = self.redis.keys("*")
        self.assertEqual(len(keys), 1)
        self.assertEqual(self.redis.type(keys[0]), "hash")
        self.assertEqual(keys[0], str(id(d)))

    def test_dict_custom_id(self):
        d = structs.Dict(name="blablebli")
        d["1"] = 2
        self.assertEqual(d.pk, "blablebli")
        keys = self.redis.keys("*")
        self.assertEqual(len(keys), 1)
        self.assertEqual(self.redis.type(keys[0]), "hash")
        self.assertEqual(keys[0], "blablebli")

    def test_initial_data(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.Dict()
        self.assertEqual(len(d), 0)
        
        d = structs.Dict([])
        self.assertEqual(len(d), 0)
        
        d = structs.Dict({})
        self.assertEqual(len(d), 0)
        
        d = structs.Dict({"a": 1})
        self.assertEqual(len(d), 1)
        self.assertEqual(d["a"], "1")

        d = structs.Dict((("c", 5), ("d", 6)))
        self.assertEqual(len(d), 2)
        self.assertEqual(d["c"], "5")
        self.assertEqual(d["d"], "6")
        
    def test_get_set_del(self):
        d = structs.Dict()
        d["a"] = 1
        self.assertTrue("a" in d)
        self.assertEqual(d["a"], "1")
        self.assertEqual(len(d), 1)
        self.assertEqual(self.redis.hget(d.pk, "a"), "1")
        self.assertEqual(self.redis.hlen(d.pk), 1)
        d["b"] = 2
        self.assertTrue("a" in d)
        self.assertEqual(d["a"], "1")
        self.assertTrue("b" in d)
        self.assertEqual(d["b"], "2")
        self.assertEqual(len(d), 2)
        self.assertEqual(self.redis.hget(d.pk, "a"), "1")
        self.assertEqual(self.redis.hget(d.pk, "b"), "2")
        self.assertEqual(self.redis.hlen(d.pk), 2)
        d["a"] = "bla"
        self.assertTrue("a" in d)
        self.assertEqual(d["a"], "bla")
        self.assertTrue("b" in d)
        self.assertEqual(d["b"], "2")
        self.assertEqual(len(d), 2)
        self.assertEqual(self.redis.hget(d.pk, "a"), "bla")
        self.assertEqual(self.redis.hget(d.pk, "b"), "2")
        self.assertEqual(self.redis.hlen(d.pk), 2)
        del d["a"]
        self.assertFalse("a" in d)
        self.assertTrue("b" in d)
        self.assertEqual(d["b"], "2")
        self.assertEqual(len(d), 1)
        self.assertEqual(self.redis.hget(d.pk, "b"), "2")
        self.assertEqual(self.redis.hlen(d.pk), 1)

    def test_get_wrong_key(self):
        d = structs.Dict()
        with self.assertRaises(KeyError) as cm:
            d["wrong key"]

    def test_keys_values_items(self):
        d = structs.Dict()
        d["a"] = 1
        self.assertEqual(d.keys(), ["a"])
        self.assertEqual(d.values(), ["1"])
        self.assertEqual(d.items(), [("a", "1")])
        self.assertEqual(d.to_dict(), {"a": "1"})
        d["b"] = 2
        self.assertEqual(d.keys(), ["a", "b"])
        self.assertEqual(d.values(), ["1", "2"])
        self.assertEqual(d.items(), [("a", "1"), ("b", "2")])
        self.assertEqual(d.to_dict(), {"a": "1", "b": "2"})
        d["c"] = 3
        self.assertEqual(d.keys(), ["a", "b", "c"])
        self.assertEqual(d.values(), ["1", "2", "3"])
        self.assertEqual(d.items(), [("a", "1"), ("c", "3"), ("b", "2")])
        self.assertEqual(d.to_dict(), {"a": "1", "b": "2", "c": "3"})
        del d["b"]
        self.assertEqual(d.keys(), ["a", "c"])
        self.assertEqual(d.values(), ["1", "3"])
        self.assertEqual(d.items(), [("a", "1"), ("c", "3")])
        self.assertEqual(d.to_dict(), {"a": "1", "c": "3"})

    def test_incrby(self):
        d = structs.Dict()
        self.assertFalse("a" in d)
        d.incrby("a", 1)
        self.assertTrue("a" in d)
        self.assertTrue(d["a"], "1")
        d.incrby("a", 1)
        self.assertTrue(d["a"], "2")
        d.incrby("a", 1.25)
        self.assertTrue(d["a"], "3.25")
        d["b"] = "text"
        with self.assertRaises(TypeError):
            d.incrby("b", 1.25)
            d.incrby("a", "not a number")

    def test_pop(self):
        d = structs.Dict()
        d["a"] = 3
        self.assertEqual(len(d), 1)
        self.assertEqual(d.pop("a"), "3")
        self.assertEqual(len(d), 0)
        self.assertFalse("a" in d)
        self.assertEqual(d.pop("a", 2), 2)
        d["a"] = 4
        self.assertEqual(d.pop("a", 2), "4")
        self.assertEqual(d.pop("b", 2), 2)
        with self.assertRaises(KeyError):
            d.pop("d")

    def test_setdefault(self):
        d = structs.Dict()
        self.assertEqual(len(d), 0)
        self.assertEqual(d.setdefault("key", 1), 1)
        self.assertEqual(len(d), 1)
        self.assertTrue("key" in d)
        self.assertEqual(d["key"], "1")
        self.assertEqual(d.setdefault("key"), "1")
        self.assertEqual(d.setdefault("key", 2), "1")
        self.assertTrue("key" in d)
        self.assertEqual(d["key"], "1")
        self.assertIsNone(d.setdefault("key2"))

    def test_update(self):
        d = structs.Dict()
        d.update((("c", 5), ("d", 6)))
        self.assertTrue(len(d), 2)
        self.assertEqual(d["c"], "5")
        self.assertEqual(d["d"], "6")

        d = structs.Dict()
        d.update(c=10, d=11, f=20)
        self.assertTrue(len(d), 2)
        self.assertEqual(d["c"], "10")
        self.assertEqual(d["d"], "11")
        self.assertEqual(d["f"], "20")

        d = structs.Dict()
        d.update()
        self.assertEqual(len(d), 0)
        d.update({})
        self.assertEqual(len(d), 0)
        d.update([])
        self.assertEqual(len(d), 0)
        d.update({"a": 1, "b": 2})
        self.assertEqual(len(d), 2)
        self.assertEqual(d["a"], "1")
        self.assertEqual(d["b"], "2")
        d.update({"b": 4, "c": 3})
        self.assertEqual(len(d), 3)
        self.assertEqual(d["a"], "1")
        self.assertEqual(d["b"], "4")
        self.assertEqual(d["c"], "3")
        d.update((("c", 5), ("d", 6)))
        self.assertEqual(len(d), 4)
        self.assertEqual(d["a"], "1")
        self.assertEqual(d["b"], "4")
        self.assertEqual(d["c"], "5")
        self.assertEqual(d["d"], "6")
        d.update(c=10, d=11, f=20)
        self.assertTrue(len(d), 5)
        self.assertEqual(d["a"], "1")
        self.assertEqual(d["b"], "4")
        self.assertEqual(d["c"], "10")
        self.assertEqual(d["d"], "11")
        self.assertEqual(d["f"], "20")


if __name__ == '__main__':
    unittest.main()