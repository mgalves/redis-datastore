#!/usr/bin/env python
# -*- coding: utf-8 -*-
import redis

REDIS = redis.Redis()


class Dict(object):
    
    def __init__(self, *args, **kwargs):
        self.pk = kwargs["name"] if "name" in kwargs and kwargs["name"] else id(self)
        self.connection = kwargs["connection"] if "connection" in kwargs and kwargs["connection"] else REDIS

        if args: # initial data
            self.update(args[0])

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

    def __init__(self, *args, **kwargs):
        self.pk = kwargs["name"] if "name" in kwargs and kwargs["name"] else id(self)
        self.connection = kwargs["connection"] if "connection" in kwargs and kwargs["connection"] else REDIS

        if args: # initial data
            self.extend(args[0])      

    def __len__(self):
        """
        LLEN
        """
        return self.connection.llen(self.pk)

    def _check_index(self, value):
        try:
            return long(value)
        except ValueError, e:
            raise TypeError("list indices must be integers")

    def __setitem__(self, index, value):
        """
        LSET
        """
        index = self._check_index(index)
        try:
            self.connection.lset(self.pk, index, value)
        except redis.exceptions.ResponseError:
            raise IndexError("list index out of range")

    def _get_range(self, start, stop):
        """
        LRANGE
        """
        # empty start equals range from first element
        if start is None and stop is None:
            return self.connection.lrange(self.pk, 0, -1)

        if not start is None and stop is None:
            start = self._check_index(start)
            return self.connection.lrange(self.pk, start, -1)

        if start is None and not stop is None:
            stop = self._check_index(stop)
            if stop == 0:
                return []
             # python end index exclusive, redis inclusive
            return self.connection.lrange(self.pk, 0, stop-1)

        if not start is None and not stop is None:
            start = self._check_index(start)
            stop = self._check_index(stop)
            if start == stop or stop == 0:
                return []
            return self.connection.lrange(self.pk, start, stop-1)


    def __getitem__(self, index_or_slice):
        """
        LINDEX / LRANGE
        """
        if type(index_or_slice) == slice:
            return self._get_range(index_or_slice.start, index_or_slice.stop)    
        else:
            index = self._check_index(index_or_slice)
            pipe = self.connection.pipeline()
            pipe.llen(self.pk)
            pipe.lindex(self.pk, index)
            llen, value = pipe.execute()
            if llen and llen > index:
                return value
            else:
                raise IndexError("list index out of range") 

    def append(self, *values):
        """
        RPUSH
        """
        if values:
            self.connection.rpush(self.pk, *values)
  
    def extend(self, other_list):
        """
        RPUSH revisited
        """
        elements = list(other_list)
        if elements:
            self.connection.rpush(self.pk, *elements)

    def insert(self, index, value):
        """
        LINSERT
        """
        index = self._check_index(index)
        pipe = self.connection.pipeline()
        pipe.llen(self.pk)
        pipe.lindex(self.pk, index)
        llen, reference_value = pipe.execute()
        if llen and llen > index:
            self.connection.linsert(self.pk, "BEFORE", reference_value, value)
        else:
            raise IndexError("list index out of range") 
     
    def push(self, value):
        """
        LPUSH
        """
        return self.connection.lpush(self.pk, value)

    def pop(self):
        """
        LPOP
        """
        return self.connection.lpop(self.pk)

    def rpop(self):
        """
        RPOP
        """
        return self.connection.rpop(self.pk)

    def trim(self, start, stop):
        """
        LTRIM
        """
        return self.connection.ltrim(self.pk, start, stop)
