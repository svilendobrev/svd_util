#!/usr/bin/env python

from adb import *

from users import test4db_users

def zsetup_extra( me):
    test4db_users._make_users()
cudb.setup_extra = test4db_users._make_users #()classmethod( setup_extra)

class sec4db( test4db_users, TEST):
    _DBNAME = 'sec4db'
    DBNAME = pfx_dbname( _DBNAME )

    doc = dict( a=3 )

    @property
    def _sec4db( me):
        return me.mgr.Sec4db( db= me.db)

    def setup( me):
        me.unsetup_db( quiet= True)
        me.db = me.mgr.open( me.DBNAME, new= True)
        me.db.save( me.doc)
    def unsetup( me, quiet =False):
        me.unsetup_db()

    def assert_eq_sec( me, **ka):
        me.assert_eq( me._sec4db.sec, ka)
    def assert_eq_all_docs( me):
        me.assert_eq_all( me.mgr.all_docs( me.db, all= True), [ me.doc ] )

    def add_user( me):
        u = me.u2.name
        u1= me.u1.name

        me.assert_eq_all_docs()
        me.assert_eq_sec()

        me._sec4db.add_user( u)
        me.assert_eq_sec( readers= dict( names= [ u] ))

        me._sec4db.add_user( u1)
        me.assert_eq_sec( readers= dict( names= [ u, u1] ))
        me.assert_eq_all_docs()

        me._sec4db.add_user( u)
        me.assert_eq_sec( readers= dict( names= [ u, u1] ))

    def del_user( me):
        u = me.u2.name
        u1= me.u1.name
        me._sec4db.add_user( u)
        me._sec4db.add_user( u1)
        me.assert_eq_sec( readers= dict( names= [ u, u1] ))

        me._sec4db.del_user( u)
        me.assert_eq_sec( readers= dict( names= [ u1] ))
        me.assert_eq_all_docs()

        me._sec4db.del_user( u1, at_least_admin =None)
        me.assert_eq_sec( readers= dict( names= [ ] ))
        me.assert_eq_all_docs()

    def del_user_at_least_admin( me):
        u = me.u2.name
        me._sec4db.add_user( u)
        me.assert_eq_sec( readers= dict( names= [ u] ))

        admin = 'admm'+u
        me._sec4db.del_user( u, at_least_admin= admin)
        me.assert_eq_sec( readers= dict( names= [ admin ] ))
        me.assert_eq_all_docs()

    def q_users( me):
        u1= me.u1.name
        u2= me.u2.name
        me.assert_eq_all_docs()
        me.assert_eq_sec()

        me._sec4db.add_user( u1)
        me.assert_eq( me._sec4db.q_users(), [ u1] )

        me._sec4db.add_user( u2)
        me.assert_eq( me._sec4db.q_users(), [ u1, u2] )

    def q_is_user( me):
        u = me.u2.name
        u1= me.u1.name
        me._sec4db.add_user( u)
        me._sec4db.add_user( u1)
        me.assert_eq_sec( readers= dict( names= [ u, u1] ))

        me.assert_eq( me._sec4db.q_is_user( u1), True)
        me.assert_eq( me._sec4db.q_is_user( u),  True)
        me.assert_eq( me._sec4db.q_is_user( u+u1), False)

        me._sec4db.del_user( u1)
        me.assert_eq( me._sec4db.q_is_user( u1), False)
        me.assert_eq( me._sec4db.q_is_user( u),  True)

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
