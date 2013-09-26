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


class TestList(unittest.TestCase):

    def setUp(self):
        self.redis = redis.Redis()
        self.redis.flushdb()

    def test_empty_list(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.List()
        self.assertEqual(len(d), 0)
        self.assertFalse(self.redis.keys("*"))
        with self.assertRaises(IndexError):
            d[0]

    def test_append_get_set(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.List(["bla"])
        keys = self.redis.keys("*")
        self.assertEqual(len(keys), 1)
        self.assertEqual(self.redis.type(keys[0]), "list")
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0], "bla")

        d.append("ble", 1, 2, "blu")
        self.assertEqual(len(d), 5)
        self.assertEqual(d[0], "bla")
        self.assertEqual(d[1], "ble")
        self.assertEqual(d[2], "1")
        self.assertEqual(d[3], "2")
        self.assertEqual(d[4], "blu")

    def test_extend(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.List(["bla"])
        d.extend({})
        self.assertEqual(len(d), 1)
        d.extend(())
        self.assertEqual(len(d), 1)
        d.extend("")
        self.assertEqual(len(d), 1)
        
        d.extend(["ble", 1, 2, "blu"])
        self.assertEqual(len(d), 5)
        self.assertEqual(d[0], "bla")
        self.assertEqual(d[1], "ble")
        self.assertEqual(d[2], "1")
        self.assertEqual(d[3], "2")
        self.assertEqual(d[4], "blu")

        d.extend({"a": 1, "b": 2})
        self.assertEqual(len(d), 7)
        self.assertEqual(d[0], "bla")
        self.assertEqual(d[1], "ble")
        self.assertEqual(d[2], "1")
        self.assertEqual(d[3], "2")
        self.assertEqual(d[4], "blu")
        self.assertEqual(d[5], "a")
        self.assertEqual(d[6], "b")
        d.extend("dfg")
        self.assertEqual(len(d), 10)
        self.assertEqual(d[0], "bla")
        self.assertEqual(d[1], "ble")
        self.assertEqual(d[2], "1")
        self.assertEqual(d[3], "2")
        self.assertEqual(d[4], "blu")
        self.assertEqual(d[5], "a")
        self.assertEqual(d[6], "b")
        self.assertEqual(d[7], "d")
        self.assertEqual(d[8], "f")
        self.assertEqual(d[9], "g")

    def test_lpop_rpop(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.List(["a", "b"])
        self.assertEqual(len(d), 2)
        self.assertEqual(d.pop(), "a")
        self.assertEqual(len(d), 1)
        self.assertEqual(d.pop(), "b")
        self.assertEqual(len(d), 0)

        d = structs.List(["a", "b", "c"])
        self.assertEqual(d.rpop(), "c")
        self.assertEqual(len(d), 2)
        self.assertEqual(d.rpop(), "b")
        self.assertEqual(len(d), 1)
        self.assertEqual(d.rpop(), "a")
        self.assertEqual(len(d), 0)

    def test_push(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.List()
        self.assertEqual(len(d), 0)
        d.push("a")
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0], "a")
        d.push("b")
        self.assertEqual(len(d), 2)
        self.assertEqual(d[0], "b")
        self.assertEqual(d[1], "a")

    def test_insert(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.List()
        with self.assertRaises(IndexError):
            d.insert(0, "c")
    
        d = structs.List(["a"])
        d.insert(0, "b")
        self.assertEqual(len(d), 2)
        self.assertEqual(d[0], "b")
        self.assertEqual(d[1], "a")
        d.insert(1, "c")
        self.assertEqual(len(d), 3)
        self.assertEqual(d[0], "b")
        self.assertEqual(d[1], "c")
        self.assertEqual(d[2], "a")

        with self.assertRaises(TypeError):
            d.insert("bla", "c")
        with self.assertRaises(IndexError):
            d.insert(3, "c")
            
    def test_range(self):
        python_list = ["0", "1", "2", "3", "4", "5", "6"]
        d = structs.List(["0", "1", "2", "3", "4", "5", "6"])

        for i in range(-10, 10):
            print i, ":", d[i:]
            self.assertEqual(d[i:], python_list[i:])

        for i in range(-10, 10):
            print ":",i, d[:i]
            self.assertEqual(d[:i], python_list[:i])

        for i in range(-7, 7):
            for j in range(-7, 7):
                print i, ":",j, d[i:j], python_list[i:j]
                self.assertEqual(d[i:j], python_list[i:j])

        # FULL RANGE
        self.assertEqual(d[:], python_list[:])

        with self.assertRaises(TypeError):
            d["b":]
        with self.assertRaises(TypeError):
            d["b":0]
        with self.assertRaises(TypeError):
            d["b":"a"]
        with self.assertRaises(TypeError):
            d[:"a"]
        with self.assertRaises(TypeError):
            d[10:"a"]

if __name__ == '__main__':
    unittest.main()