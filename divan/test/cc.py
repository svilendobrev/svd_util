#!/usr/bin/env python

from adb import *
from users import test4db_users
#cudb.setup_extra = test4db_users._make_users
from data.cu import Channel4user

class cc( test4db_users, TEST):

    u = test4db_users.u3.name
    DBNAME = Channel4user._cc_name( u)

    do_unsetup = True
    def setup( me):
        me.unsetup_db( quiet= True)
        me.cc = me.mgr.Channel4user( me.u)
        me._make_users()

    def unsetup( me):
        me.unsetup_db( quiet= not me.do_unsetup)
        me._destroy_users()

    def _all_docs( me):
        return me.cc._all_docs()
    def assert_eq_all_docs( me, expect ):
        me.assert_eq_set( me._all_docs(), expect )

    def assert_eq_sec_users( me, expect):
        me.assert_eq_set( me.mgr.Sec4db( db= me.cc.db ).q_users(), expect)

    ########

    def ctor_does_not_create( me):
        assert me.DBNAME not in me.mgr.server
        me.do_unsetup = False

    def user_from_name( me):
        me.create()
        me.assert_eq( Channel4user._user_from_name( me.cc.dbname ), me.u )

    def lazy_db_no_autocreate( me):
        assert me.DBNAME not in me.mgr.server
        me.assertRaises( ResourceNotFound, lambda: me.cc.db )
        me.do_unsetup = False

    def create( me, update_user =True):
        assert me.DBNAME not in me.mgr.server
        u = me.u
        ru = me.users.q_user( u)
        me.assert_eq_1( ru, dict( name= u,
                control_channel= Missing ))

        me.cc.create( new= True, update_user= update_user )
        me.cc.db

        me.assert_eq( me.cc.q_user(), u)    #assumes create( update_sec=True)
        me.assert_eq_all_docs( [] )
        me.assert_eq_sec_users( [ u ] )

        ru = me.users.q_user( u)
        me.assert_eq_1( ru, dict( name= u,
                control_channel= update_user and me.DBNAME or Missing ))

    def create_no_upd_user( me):
        me.create( update_user= False)

    def disable( me):
        me.create()
        me.cc.disable()
        me.assert_eq_sec_users( [ cu.Sec4db._admin ] )

    def destroy( me):
        me.create()
        assert me.DBNAME in me.mgr.server

        me.cc.destroy()

        assert me.DBNAME not in me.mgr.server
        me.do_unsetup = False

    def destroy_without_create_does_nothing( me):
        assert me.DBNAME not in me.mgr.server

        #actualy check it does not create THEN destroy
        def dontcall( *a,**ka): assert 0, 'dontcall '+str(locals())
        s = me.mgr.server
        org = s.create
        s.create = dontcall
        try:
            me.cc.destroy()
        finally:
            s.create = org

        assert me.DBNAME not in me.mgr.server
        me.do_unsetup = False

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
