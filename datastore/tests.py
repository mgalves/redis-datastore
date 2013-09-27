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
        keys = self.redis.keys("*")
        self.assertEqual(len(keys), 1)
        self.assertEqual(self.redis.type(keys[0]), "hash")
        self.assertEqual(keys[0], d.pk)

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



class TestSet(unittest.TestCase):

    def setUp(self):
        self.redis = redis.Redis()
        self.redis.flushdb()

    def test_empty_list(self):
        self.assertFalse(self.redis.keys("*"))
        d = structs.Set()
        self.assertEqual(len(d), 0)
        self.assertFalse(1 in d)
        self.assertFalse(self.redis.keys("*"))

    def test_list_constructor(self):
        self.assertFalse(self.redis.keys("*"))
        d1 = structs.Set(["bla"])
        keys = self.redis.keys("*")
        self.assertEqual(len(keys), 1)
        self.assertEqual(self.redis.type(keys[0]), "set")
        self.assertEqual(len(d1), 1)
        self.assertTrue("bla" in d1)
        d2 = structs.Set("bla")
        keys = self.redis.keys("*")
        self.assertEqual(len(keys), 2)
        self.assertEqual(len(d2), 3)
        self.assertTrue("b" in d2)
        self.assertTrue("l" in d2)
        self.assertTrue("a" in d2)
        
    def test_add_remove(self):
        d = structs.Set()
        self.assertEqual(len(d), 0)
        d.add("a")
        self.assertEqual(len(d), 1)
        self.assertTrue("a" in d)
        d.add("b", "c", "d")
        self.assertEqual(len(d), 4)
        self.assertTrue("a" in d)
        self.assertTrue("b" in d)
        self.assertTrue("c" in d)
        self.assertTrue("d" in d)
        d.discard("d")
        self.assertEqual(len(d), 3)
        self.assertTrue("a" in d)
        self.assertTrue("b" in d)
        self.assertTrue("c" in d)
        self.assertTrue("d" not in d)
        d.discard("f")
        self.assertEqual(len(d), 3)
        d.remove("b")
        self.assertEqual(len(d), 2)
        self.assertTrue("a" in d)
        self.assertTrue("b" not in d)
        self.assertTrue("c" in d)
        self.assertTrue("d" not in d)
        with self.assertRaises(KeyError):
            d.remove("f")

    def test_random_pop(self):
        d = structs.Set("abcde")
        self.assertEqual(len(d.random()), 1)
        for i in range(1, 6):
            random = d.random(count=i)
            self.assertEqual(len(random), i)
            for r in random:
                self.assertTrue(r in d)
    
        for i in range(1, 6):
            element = d.pop()
            self.assertTrue(element in ["a", "b", "c", "d", "e"])
            self.assertEqual(len(d), 5-i)
            self.assertTrue(element not in d)

        self.assertEqual(len(d), 0)
        with self.assertRaises(KeyError):
            d.pop()

    def test_intersection_update(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("bc")
        new_set = d1.intersection_update(d2)
        self.assertEqual(new_set, d1)
        self.assertEqual(len(d1), 2)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" not in d1)
        self.assertTrue("b" not in d1)
        new_set = d1.intersection_update(d3)
        self.assertEqual(new_set, d1)
        self.assertEqual(len(d1), 1)
        self.assertTrue("c" in d1)
        self.assertTrue("d" not in d1)
        self.assertTrue("a" not in d1)
        self.assertTrue("b" not in d1)
        new_set = d2.intersection_update(d1, d3)
        self.assertEqual(new_set, d2)
        self.assertEqual(len(d2), 1)
        self.assertTrue("c" in d2)
        self.assertTrue("d" not in d2)
        self.assertTrue("a" not in d2)
        self.assertTrue("b" not in d2)

        with self.assertRaises(TypeError):
            d2.intersection_update(["bla"])
        with self.assertRaises(TypeError):
            d2.intersection_update(d1, d2, ["bla"])

    def test_intersection(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("bc")
        new_set = d1.intersection(d2)
        self.assertFalse(new_set == d1)
        self.assertEqual(len(d1), 4)
        self.assertEqual(len(new_set), 2)
        self.assertTrue("c" in new_set)
        self.assertTrue("d" in new_set)
        self.assertTrue("a" not in new_set)
        self.assertTrue("b" not in new_set)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        new_set = d2.intersection(d1, d3)
        self.assertEqual(len(d2), 2)
        self.assertEqual(len(new_set), 1)
        self.assertTrue("c" in new_set)
        self.assertTrue("d" not in new_set)
        self.assertTrue("a" not in new_set)
        self.assertTrue("b" not in new_set)
        self.assertTrue("c" in d2)
        self.assertTrue("d" in d2)
        self.assertTrue("a" not in d2)
        self.assertTrue("b" not in d2)

        with self.assertRaises(TypeError):
            d2.intersection(["bla"])
        with self.assertRaises(TypeError):
            d2.intersection(d1, d2, ["bla"])

    def test_difference_update(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("bc")
        new_set = d1.difference_update(d2)
        self.assertEqual(new_set, d1)
        self.assertEqual(len(d1), 2)
        self.assertTrue("c" not in d1)
        self.assertTrue("d" not in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        new_set = d1.difference_update(d3)
        self.assertEqual(new_set, d1)
        self.assertEqual(len(d1), 1)
        self.assertTrue("c" not in d1)
        self.assertTrue("d" not in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" not in d1)
        new_set = d2.difference_update(d1)
        self.assertEqual(new_set, d2)
        self.assertEqual(len(d2), 2)
        self.assertTrue("c" in d2)
        self.assertTrue("d" in d2)

        with self.assertRaises(TypeError):
            d2.difference_update(["bla"])
        with self.assertRaises(TypeError):
            d2.difference_update(d1, d2, ["bla"])

    def test_difference(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("bc")
        new_set = d1.difference(d2)
        self.assertFalse(new_set == d1)
        self.assertEqual(len(d1), 4)
        self.assertEqual(len(new_set), 2)
        self.assertTrue("c" not in new_set)
        self.assertTrue("d" not in new_set)
        self.assertTrue("a" in new_set)
        self.assertTrue("b" in new_set)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        new_set = d1.difference(d3)
        self.assertFalse(new_set == d1)
        self.assertEqual(len(d1), 4)
        self.assertEqual(len(new_set), 2)
        self.assertTrue("c" not in new_set)
        self.assertTrue("d" in new_set)
        self.assertTrue("a" in new_set)
        self.assertTrue("b" not in new_set)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        new_set = d2.difference(d1)
        self.assertEqual(len(d2), 2)
        self.assertEqual(len(new_set), 0)
        self.assertTrue("c" in d2)
        self.assertTrue("d" in d2)
        self.assertTrue("a" not in d2)
        self.assertTrue("b" not in d2)

        with self.assertRaises(TypeError):
            d2.difference(["bla"])
        with self.assertRaises(TypeError):
            d2.difference(d1, d2, ["bla"])

    def test_update(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("bcef")
        d4 = structs.Set("efg")
        new_set = d1.update(d2)
        self.assertEqual(new_set, d1)
        self.assertEqual(len(d1), 4)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        new_set = d1.update(d3)
        self.assertEqual(new_set, d1)
        self.assertEqual(len(d1), 6)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        self.assertTrue("e" in d1)
        self.assertTrue("f" in d1)
        new_set = d2.update(d3, d4)
        self.assertEqual(new_set, d2)
        self.assertEqual(len(d2), 6)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        self.assertTrue("e" in d1)
        self.assertTrue("f" in d1)

        with self.assertRaises(TypeError):
            d2.update(["bla"])
        with self.assertRaises(TypeError):
            d2.update(d1, d2, ["bla"])

    def test_union(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("bce")
        new_set = d1.union(d2)
        self.assertFalse(new_set == d1)
        self.assertEqual(len(d1), 4)
        self.assertEqual(len(new_set), 4)
        self.assertTrue("c" in new_set)
        self.assertTrue("d" in new_set)
        self.assertTrue("a" in new_set)
        self.assertTrue("b" in new_set)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        new_set = d1.union(d3)
        self.assertFalse(new_set == d1)
        self.assertEqual(len(d1), 4)
        self.assertEqual(len(new_set), 5)
        self.assertTrue("c" in new_set)
        self.assertTrue("d" in new_set)
        self.assertTrue("a" in new_set)
        self.assertTrue("b" in new_set)
        self.assertTrue("e" in new_set)
        self.assertTrue("c" in d1)
        self.assertTrue("d" in d1)
        self.assertTrue("a" in d1)
        self.assertTrue("b" in d1)
        new_set = d2.union(d1, d3)
        self.assertEqual(len(d2), 2)
        self.assertEqual(len(new_set), 5)

        with self.assertRaises(TypeError):
            d2.union(["bla"])
        with self.assertRaises(TypeError):
            d2.union(d1, d2, ["bla"])

    def test_disjoint(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("abcd")
        d4 = structs.Set("fgh")
        self.assertFalse(d1.isdisjoint(d2))
        self.assertFalse(d1.isdisjoint(d3))
        self.assertFalse(d2.isdisjoint(d1))
        self.assertFalse(d2.isdisjoint(d3))
        self.assertFalse(d3.isdisjoint(d2))
        self.assertFalse(d3.isdisjoint(d1))

        self.assertTrue(d1.isdisjoint(d4))
        self.assertTrue(d4.isdisjoint(d1))
        self.assertTrue(d2.isdisjoint(d4))
        self.assertTrue(d4.isdisjoint(d2))
        self.assertTrue(d3.isdisjoint(d4))
        self.assertTrue(d4.isdisjoint(d3))
        with self.assertRaises(TypeError):
            d1.isdisjoint(["bla"])

    def test_superset(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("abcd")
        d4 = structs.Set("fgh")
        d5 = structs.Set("cde")
        self.assertTrue(d1.issuperset(d2))
        self.assertTrue(d1.issuperset(d3))
        self.assertFalse(d1.issuperset(d4))
        self.assertFalse(d1.issuperset(d5))
        self.assertFalse(d2.issuperset(d1))
        self.assertFalse(d2.issuperset(d3))
        self.assertFalse(d2.issuperset(d4))
        self.assertFalse(d2.issuperset(d5))
        self.assertTrue(d3.issuperset(d2))
        self.assertTrue(d3.issuperset(d1))
        self.assertFalse(d3.issuperset(d4))
        self.assertFalse(d3.issuperset(d5))
        self.assertTrue(d5.issuperset(d2))
        self.assertTrue(d1 >= d2)
        self.assertTrue(d1 >= d3)
        self.assertFalse(d1 >= d4)
        self.assertFalse(d2 >= d1)
        self.assertFalse(d2 >= d3)
        self.assertFalse(d2 >= d4)
        self.assertTrue(d3 >= d2)
        self.assertTrue(d3 >= d1)
        self.assertFalse(d3 >= d4)
        with self.assertRaises(TypeError):
            d1.issuperset(["bla"])
        with self.assertRaises(TypeError):
            d1 >= ["bla"]

    def test_proper_superset(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("abcd")
        d4 = structs.Set("fgh")
        d5 = structs.Set("cde")
        self.assertTrue(d1 > d2)
        self.assertFalse(d1 > d3)
        self.assertFalse(d1 > d4)
        self.assertFalse(d1 > d5)
        self.assertFalse(d2 > d1)
        self.assertFalse(d2 > d3)
        self.assertFalse(d2 > d4)
        self.assertFalse(d2 > d5)
        self.assertTrue(d3 > d2)
        self.assertFalse(d3 > d1)
        self.assertFalse(d3 > d4)
        self.assertTrue(d5 > d2)
        with self.assertRaises(TypeError):
            d1 > ["bla"]

    def test_subset(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("abcd")
        d4 = structs.Set("fgh")
        d5 = structs.Set("cde")
        self.assertFalse(d1.issubset(d2))
        self.assertTrue(d1.issubset(d3))
        self.assertFalse(d1.issubset(d4))
        self.assertFalse(d1.issubset(d5))
        self.assertTrue(d2.issubset(d1))
        self.assertTrue(d2.issubset(d3))
        self.assertFalse(d2.issubset(d4))
        self.assertTrue(d2.issubset(d5))
        self.assertFalse(d3.issubset(d2))
        self.assertTrue(d3.issubset(d1))
        self.assertFalse(d3.issubset(d4))
        self.assertFalse(d3.issubset(d5))
        self.assertFalse(d5.issubset(d2))
        self.assertFalse(d1 <= d2)
        self.assertTrue(d1 <= d3)
        self.assertFalse(d1 <= d4)
        self.assertTrue(d2 <= d1)
        self.assertTrue(d2 <= d3)
        self.assertFalse(d2 <= d4)
        self.assertFalse(d3 <= d2)
        self.assertTrue(d3 <= d1)
        self.assertFalse(d3 <= d4)
        with self.assertRaises(TypeError):
            d1.issubset(["bla"])
        with self.assertRaises(TypeError):
            d1 <= ["bla"]

    def test_proper_subset(self):
        d1 = structs.Set("abcd")
        d2 = structs.Set("cd")
        d3 = structs.Set("abcd")
        d4 = structs.Set("fgh")
        d5 = structs.Set("cde")
        self.assertFalse(d1 < d2)
        self.assertFalse(d1 < d3)
        self.assertFalse(d1 < d4)
        self.assertFalse(d1 < d5)
        self.assertTrue(d2 < d1)
        self.assertTrue(d2 < d3)
        self.assertFalse(d2 < d4)
        self.assertTrue(d2 < d5)
        self.assertFalse(d3 < d2)
        self.assertFalse(d3 < d1)
        self.assertFalse(d3 < d4)
        self.assertFalse(d5 < d2)
        with self.assertRaises(TypeError):
            d1 < ["bla"]

    def test_members(self):
        d1 = structs.Set("a")
        self.assertEqual(d1.members(), set(["a"]))
        d1 = structs.Set("abcd")
        self.assertEqual(d1.members(), set(["a", "b", "c", "d"]))
        d1 = structs.Set()
        self.assertEqual(d1.members(), set())

    def test_momve_member(self):
        d1 = structs.Set(["a", "b"])
        d2 = structs.Set()
        self.assertTrue("b" not in d2)
        self.assertEqual(len(d2), 0)
        self.assertTrue("b" in d1)
        self.assertEqual(len(d1), 2)
        d1.move("b", d2)
        self.assertTrue("b" in d2)
        self.assertEqual(len(d2), 1)
        self.assertTrue("b" not in d1)
        self.assertEqual(len(d1), 1)
        with self.assertRaises(TypeError):
            d1.move("a", "bla")
        with self.assertRaises(KeyError):
            d1.move("bla", d2)

if __name__ == '__main__':
    unittest.main()