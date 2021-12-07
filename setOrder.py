# sdobrev 2007
'ordered set - by-item-creation'
from __future__ import print_function #,unicode_literals

try:
    import collections.abc
    has_collections = True
except:
    has_collections = False
else:   #this seems copypasted from somewhere
  class OrderedSet( collections.OrderedDict, collections.abc.MutableSet):
    def __init__(self, items=()):
        collections.OrderedDict.__init__(self, [(i, True) for i in items])

    def update(self, *args):
        for s in args:
            for e in s:
                self.add(e)
    def add(self, elem):
        self[elem] = None
    def discard(self, elem):
        self.pop(elem, None)
    def __le__(self, other):
        return all(e in other for e in self)
    def __lt__(self, other):
        return self <= other and self != other
    def __ge__(self, other):
        return all(e in self for e in other)
    def __gt__(self, other):
        return self >= other and self != other
    def __repr__(self):
        return 'OrderedSet([%s])' % (', '.join(map(repr, self.keys())))
    def __str__(self):
        return '{%s}' % (', '.join(map(repr, self.keys())))
    difference = property(lambda self: self.__sub__)
    difference_update = property(lambda self: self.__isub__)
    intersection = property(lambda self: self.__and__)
    intersection_update = property(lambda self: self.__iand__)
    issubset = property(lambda self: self.__le__)
    issuperset = property(lambda self: self.__ge__)
    symmetric_difference = property(lambda self: self.__xor__)
    symmetric_difference_update = property(lambda self: self.__ixor__)
    union = property(lambda self: self.__or__)

if not has_collections:     # pre py2.6?
  class OrderedSet_raw(set):
    def __init__(self, d=None, **kwargs):
        self._list = []
        if d: self.update( d, **kwargs)

    def add(self, key):
        if key not in self:
            self._list.append(key)
        set.add( self, key)

    def remove( self, element):
        set.remove( self, element)
        self._list.remove( element)

    def discard( self, element):
        try:
            set.remove( self, element)
        except KeyError: pass
        else:
            self._list.remove( element)

    def clear(self):
        set.clear( self)
        self._list=[]

    def __iter__(self): return iter(self._list)

    def update(self, iterable):
        add = self.add
        for i in iterable: add(i)
        return self

    def __repr__( self):
        return '%s(%r)' % (self.__class__.__name__, self._list)
    __str__ = __repr__

    def union(self, other):
        result = self.__class__(self)
        result.update(other)
        return result
    __or__ = union
    def intersection(self, other):
        return self.__class__( a for a in self if a in other)
        r = self.__class__()
        rl = r._list = [ a for a in self if a in other]
        set.update( rl)
        return r
    __and__ = intersection
    def symmetric_difference(self, other):
        result = self.__class__( a for a in self if a not in other)
        result.update( a for a in other if a not in self)
        return result
    __xor__ = symmetric_difference

    def difference(self, other):
        return self.__class__( a for a in self if a not in other)
    __sub__ = difference

    __ior__ = update

    def intersection_update(self, other):
        set.intersection_update( self, other)
        self._list = [ a for a in self._list if a in other]
        return self
    __iand__ = intersection_update

    def symmetric_difference_update(self, other):
        set.symmetric_difference_update( self, other)
        self._list =  [ a for a in self._list if a in self]
        self._list += [ a for a in other._list if a in self]
        return self
    __ixor__ = symmetric_difference_update

    def difference_update(self, other):
        set.difference_update( self, other)
        self._list = [ a for a in self._list if a in self]
        return self
    __isub__ = difference_update

if not has_collections: OrderedSet = OrderedSet_raw

def _test():
    for OS in [OrderedSet, OrderedSet_raw]:
        print( OS)
        def init():
            a = OS( [1,3,5,18] )
            b = OS( [5,2,3] )
            return a,b

        a,b = init()
        print( a&b)
        assert list(a&b) == [3,5] or list(a&b) == [5,3] #XXX ???
        a &= b
        print( a)
        assert list(a) == [3,5] or list(a) == [5,3]     #XXX sets.Set is wrong here

        a,b = init()
        print( a|b)
        assert list(a|b) == [1,3,5,18,2]
        a |= b
        assert list(a) == [1,3,5,18,2]

        a,b = init()
        print( a-b)
        assert list(a-b) == [1,18]
        a-=b
        assert list(a) == [1,18]

        a,b = init()
        print( a^b)
        assert list(a^b) == [1,18,2]
        a ^= b
        assert list(a) == [1,18,2]
    print( 'ok')

if __name__ == '__main__':
    _test()
# vim:ts=4:sw=4:expandtab
