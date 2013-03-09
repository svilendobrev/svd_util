#!/usr/bin/env python
from adb import *

#TODO does not need be Channel4user.. can be anything Base
TYPE = 'hoho'
imixin = cu.itemset_mixin( type= TYPE, dbkind= cu.Channel4user._KIND)
class bimixin( cu.Channel4user_mixin, imixin, cu.Base):
    #def __init__( me, **ka): me._open( **ka)
    __init__ = cu.Channel4user_mixin._init4owner

class Mgr( cu.Mgr):
    _Items = bimixin
    def Items( me, **ka):
        return cu.Channel4user_mixin._factory( me._Items, me.Channel4user, **ka)

class Titemset( test4db, TEST):
    maxDiff = None
    def _ITEMS( me, **ka): return me.mgr.Items( **ka)
    def _setup( me):
        u = 'usr'
        me.cc = me.mgr.Channel4user( u)
        me.cc.destroy( update_user= False)
        me.cc.create( new= True, update_user= False, update_sec= False)
        me.i = me._ITEMS( owner= u)
    def setup( me):
        me.TYPE = me.i.TYPE

    def assert_eq_all_docs( me, expect ):
        me.assert_eq_all( me.i._all_docs(), expect )

    def add_item( me):
        item = 'alala'
        me.assert_eq( me.cc._all_docs(), [])
        me.i.add_item( item )

        all = [ dict( type= me.TYPE, _id= item) ]
        me.assert_eq_all( me.cc._all_docs(), all)
        me.assert_eq_all_docs( all)
        me.assert_eq_all( me.i.q_items(), [ item ])
        return item

    def has_i( me):
        a = me.add_item()
        me.assert_eq( me.i.q_has_item( a), True)
        me.assert_eq( me.i.q_has_item( a+'a'), False)

    def q_items( me):
        items = [ 'aa', 'bb']
        for i in items:
            me.i.add_item( i)
        me.assert_eq_all_docs( [ dict( type= me.TYPE, _id= x) for x in items])
        me.assert_eq( me.i.q_items(), items)
        return items

    def del_item( me):
        items = me.q_items()
        me.i.del_item( items[0])
        me.assert_eq_all_docs( [ dict( type= me.TYPE, _id= items[-1] )])

if __name__ == '__main__':
    cudb.Mgr = Mgr
    main_no_users()

# vim:ts=4:sw=4:expandtab
