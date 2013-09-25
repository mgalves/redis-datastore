#!/usr/bin/env python
# -*- coding: utf-8 -*-
import redis

REDIS = redis.Redis()


class Dict(object):
    
    def __init__(self, name=None, connection=None):
        self.pk = name if name else id(self)
        self.connection = connection if connection else REDIS

    def __setitem__(self, key, value):
        """
        HSET
        """
        self.connection.hset(self.pk, key, value)

    def __getitem__(self, key):
        """
        HGET
        """
        pipe = self.connection.pipeline()
        pipe.hexists(self.pk, key)
        pipe.hget(self.pk, key)
        key_exists, key_value = pipe.execute()
        if key_exists:
            return key_value
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        """
        HDEL
        """
        self.connection.hdel(self.pk, key)

    def __contains__(self, key):
        """
        HEXISTS
        """
        return self.connection.hexists(self.pk, key)

    def __len__(self):
        """
        HLEN
        """
        return self.connection.hlen(self.pk)

    def clear(self):
        """
        Remove all items from the dictionary.
        """
        self.connection.delete(self.pk)

    def to_dict(self):
        """
        HGETALL

        Return a dict instance with the same key/value pairs
        """
        return self.connection.hgetall(self.pk)

    def get(self, key, *args):
        """
        HGET with sugar.

        Return the value for key if key is in the dictionary, else default. 
        If default is not given, it defaults to None, so that this method never raises a KeyError.
        """
        default = args[0] if args else None
        value = self.connection.hget(self.pk, key)
        return value if value else default    

    def items(self):
        """
        HGETALL

        Return a copy of the dictionary’s list of (key, value) pairs.
        """
        return [(k, v) for k, v in self.connection.hgetall(self.pk).iteritems()]

    def keys(self):
        """
        HKEYS

        Return a copy of the dictionary’s list of keys. See the note for dict.items().
        """
        return self.connection.hkeys(self.pk)
        
    def pop(self, key, *args):
        """
        If key is in the dictionary, remove it and return its value, else return default. 
        If default is not given and key is not in the dictionary, a KeyError is raised.
        """
        pipe = self.connection.pipeline()
        pipe.hexists(self.pk, key)
        pipe.hget(self.pk, key)
        pipe.hdel(self.pk, key)
        key_exists, key_value, status = pipe.execute()

        if key_exists: # Key exists...
            return key_value # return value. Already removed
        else:
            if args:
                return args[0] # default value
            else:
                raise KeyError(key)

    def setdefault(self, key, *args):
        """
        HSETNX

        If key is in the dictionary, return its value. 
        If not, insert key with a value of default and return default. default defaults to None.
        """
        default = args[0] if args else None
        pipe = self.connection.pipeline()
        pipe.hexists(self.pk, key)
        pipe.hget(self.pk, key)
        pipe.hsetnx(self.pk, key, default)
        key_exists, key_value, status = pipe.execute()
        return key_value if key_exists else default

    def update(self, *args, **kwargs):
        """
        HMSET

        Update the dictionary with the key/value pairs from other, overwriting existing keys. Return None.
        update() accepts either another dictionary object or an iterable of key/value pairs 
        (as tuples or other iterables of length two). 
        If keyword arguments are specified, the dictionary is then updated with those key/value pairs: 
        d.update(red=1, blue=2).
        """
        pipe = self.connection.pipeline()

        for arg in args:
            _type = type(arg)
            if _type == dict:
                if arg:
                    pipe.hmset(self.pk, arg)
            elif _type == list or _type == tuple:
                for tup in arg:
                    pipe.hset(self.pk, tup[0], tup[1])

        if kwargs:
            pipe.hmset(self.pk, kwargs)

        pipe.execute()

    def values(self):
        """
        HVALS

        Return a copy of the dictionary’s list of values.
        """
        return self.connection.hvals(self.pk)


    def incrby(self, key, value=1):
        """
        HINCRBY
        HINCRBYFLOAT

        Increment a key by value
        """
        if type(value) == int:
            op = self.connection.hincrby
        elif type(value) == float:
            op = self.connection.hincrbyfloat
        else:
            raise TypeError("value must be int or float")

        try:
            op(self.pk, key, value)
        except redis.exceptions.ResponseError, e:
            raise TypeError("key's value must be int or float")


class Set(object):
    pass


class SortedSet(object):
    pass


class List(object):

    def __init__(self, name=None, connection=None):
        self.pk = name if name else id(self)
        self.connection = connection if connection else REDIS

    def __len__(self):
        return self.connection.llen(self.pk)

    def __setitem__(self, index, value):
        try:
            index = long(index)
        except ValueError, e:
            raise TypeError("list indices must be integers")
        try:
            self.connection.lset(self.pk, index, value)
        except redis.exceptions.ResponseError:
            raise IndexError("list index out of range")


    def _slice(self, slice):
        start = int(index_or_slice.start) if index_or_slice.start else 0
        stop = index_or_slice.stop
        step = index_or_slice.step

    def __getitem__(self, index_or_slice):
        if type(index_or_slice) == slice:
            return self._slice(index_or_slice)    
        else:
            try:
                index = long(index_or_slice)
            except ValueError, e:
                raise TypeError("list indices must be integers")
            
            pipe = self.connection.pipeline()
            pipe.llen(self.pk)
            pipe.lindex(self.pk, index)
            llen, value = pipe.execute()
            if llen and llen > index:
                return value
            else:
                raise IndexError("list index out of range") 

    def append(self, *values):
        if len(values) == 1:
            self.connection.rpush(self.pk, values[0])
        else:
            pipe = self.connection.pipeline()
            for value in values:
                pipe.rpush(self.pk, value)
            pipe.execute()              

    def extend(l):
        i = list(l)
        self.connection.rpush(self.pk, *i)

    def insert(i, x):
        pass

    def remove(x):
        pass

    def pop(i):
        pass

    def index(x):
        pass

    def count(x):
        pass
