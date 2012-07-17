#s.dobrev 2k4
'ordered dictionary (by-item-creation)'

from __future__ import generators

class dictOrder( dict):
    __slots__ = [ 'order' ]
    def __init__( me, *args, **kargs):
        dict.__init__( me)
        me.order = []
        me.update( *args, **kargs)
        #dict.__init__ is probably faster
    def update( me, *args, **kargs):
        seti = me.__setitem__
        if args:
            arg = args[0]
            if isinstance( arg, dict): arg = arg.iteritems()
            for k,v in arg: seti( k,v)      #iterable, retain order
        for k,v in kargs.items():
            seti( k,v)      #some order

    def __setitem__( me, k, v):
        if k not in me:
            me.order.append( k)
        return dict.__setitem__( me, k,v)
    def keys( me):
        return me.order[:]              #copy()
    def values( me):
        return list( me.itervalues())   #copy()
    def items( me):
        return list( me.iteritems() )   #copy()
    def iterkeys( me):
        return iter( me.order)
    __iter__ = iterkeys
    def itervalues( me):
        geti = me.__getitem__
        for k in me.order: yield geti(k)
    def iteritems( me):
        geti = me.__getitem__
        for k in me.order: yield k,geti(k)
    def __delitem__( me, k):
        dict.__delitem__( me, k)
        me.order.remove( k)
    def copy( me):
        return me.__class__( me)
    def clear( me):
        dict.clear( me)
        me.order[:] = []
    def __str__( me):
        r = me.__class__.__name__ + '{'
        for k in me.order:
            r += ' '+str(k)+': '+str(me[k])+','
        return r+'}'
    def __repr__( me):
        return me.__class__.__name__ + '( '+repr( me.items() )+' )'
    def setdefault( me, k, v =None):
        if k in me: v = me[k]
        else:
            me.order.append( k)
            dict.__setitem__( me, k,v)
        return v
    #non-dict
    def replace( me, k, knew, v):
        dict.__delitem__( me, k)
        i = me.order.index( k)
        me.order[i] = knew
        dict.__setitem__( me, knew,v)
    def replace_index( me, k, knew):
        me.replace( k, knew, me[k])

    def pop( me, *args):
        if not args:
            key = me.order.pop()       #raise proper indexerror
            result = dict.pop( me, key)
        else:
            found = args[0] in me
            result = dict.pop( me, *args)    #raise proper keyerror
            if found: me.order.remove( args[0])
        return result
    def popitem( me):
        k,v = dict.popitem( me)     #will raise if emtpy
        me.order.remove( k)
        return k,v

    @classmethod
    def fromkeys( klas, seq, value=None):
        return klas( (k,value) for k in seq )

class dictOrderAttr( dictOrder):    #not tested
    __slots__ = ()
    def __setattr__( me, name, value):
        if name in me.__slots__: return object.__setattr__( me, name, v)
        me[ name ] = value
    def __getattr__( me, name):
        try: return me[ name ]
        except KeyError:
            raise AttributeError( name)

#class dictOrderStatic( dictOrder):
#    __setitem__ = dict.__setitem__

if __name__ == '__main__':
    do = dictOrder()
    d = {}
    order = [ 2,123,1,70, 0]
    for k in order:
        d[k] = do[k] = k

    print order
    #print 'str,repr'
    #print do, repr(do)
    #print d,  repr(d)

    for m in ['__str__', '__repr__', 'keys', 'values', 'items', ]:
        print m
        print getattr( do, m)()
        print getattr( d, m)()

    print 'del 1'
    del do[1]
    del d[1]
    print do.keys()
    print d.keys()

    print 'iterkeys'
    for k in do.iterkeys(): print k,
    print

    print 'copy+del'
    z = do.copy()
    del z[70]
    print do.keys()
    print z.keys()

    for ctor in [dictOrder, dict]:
        print  ctor({'one': 2, 'two': 3}), 'dict'
        print  ctor({'one': 2, 'two': 3}.items()), 'dict.items'
        print  ctor({'one': 2, 'two': 3}.iteritems()), 'dict.iteritems'
        print  ctor(zip(('one', 'two'), (2, 3))), 'zip/list ascend'
        print  ctor([['two', 3], ['one', 2]]), 'list descend'
        print  ctor(one=2, two=3), 'key-args'
        print  ctor([(['one', 'two'][i-2], i) for i in (2, 3)]), 'list ascend'

# vim:ts=4:sw=4:expandtab

