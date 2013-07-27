#!/usr/bin/env python

from adb import *

from users import test4db_users
import operator

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

    AUTOADMIN = True

    def setup( me):
        me.unsetup_db( quiet= True)
        if not me.AUTOADMIN:
            if me.DBNAME not in me.mgr.sec_exclude['names']:
                me.mgr.sec_exclude['names'] = list( me.mgr.sec_exclude['names'] ) + [ me.DBNAME ]
        me.db = me.mgr.open( me.DBNAME, new= True)
        me.db.save( me.doc)
    def unsetup( me, quiet =False):
        me.unsetup_db()

    @staticmethod
    def names2sec( names): return dict( readers= dict( names= names))
    @classmethod
    def _secdict( me, *ab):
        return me.names2sec( reduce( operator.__or__,
                (set( a.get( 'readers', {}).get( 'names', ())) for a in ab )
                ))

    _admin = [ cu.Sec4db._admin ]
    def assert_eq_sec( me, names, noautoadmin =False):
        if me.AUTOADMIN and not noautoadmin:
            names = set( names).union( me._admin)
        exp = me.names2sec( set( names) )

        r = me._sec4db.sec
        if isinstance( r.get('readers'), dict):
            if isinstance( r['readers'].get('names'), (list,tuple)):
                r['readers']['names'] = set( r['readers']['names'] )
        #if not names:
        #    r['readers']['names'] = set( r['readers']['names'] )
        if not names and not r: pass
        else:
            me.assert_eq( r, exp)
    def assert_eq_sec_flat( me, r, names):
        if me.AUTOADMIN:
            names = list( names ) + me._admin
        me.assert_eq_set( r, names )

    def assert_eq_all_docs( me):
        me.assert_eq_all( me.mgr.all_docs( me.db, all= True), [ me.doc ] )

    def add_user( me):
        u = me.u2.name
        u1= me.u1.name

        me.assert_eq_all_docs()
        me.assert_eq_sec( [] )

        me._sec4db.add_user( u)
        me.assert_eq_sec( [ u] )

        me._sec4db.add_user( u1)
        me.assert_eq_sec( names= [ u, u1] )
        me.assert_eq_all_docs()

        me._sec4db.add_user( u)
        me.assert_eq_sec( names= [ u, u1] )

    def del_user( me):
        u = me.u2.name
        u1= me.u1.name
        me._sec4db.add_user( u)
        me._sec4db.add_user( u1)
        me.assert_eq_sec( names= [ u, u1] )

        me._sec4db.del_user( u)
        me.assert_eq_sec( names= [ u1] )
        me.assert_eq_all_docs()

        me._sec4db.del_user( u1, at_least_admin =None)
        me.assert_eq_sec( names= [] )
        me.assert_eq_all_docs()

    def del_user_at_least_admin( me):
        if me.AUTOADMIN: return
        u = me.u2.name
        me._sec4db.add_user( u)
        me.assert_eq_sec( names= [ u] )

        admin = 'admm'+u
        me._sec4db.del_user( u, at_least_admin= admin)
        me.assert_eq_sec( names= [ admin ])
        me.assert_eq_all_docs()

    def q_users( me):
        u1= me.u1.name
        u2= me.u2.name
        me.assert_eq_all_docs()
        me.assert_eq_sec( [] )

        me._sec4db.add_user( u1)
        me.assert_eq_sec_flat( me._sec4db.q_users(), [ u1] )

        me._sec4db.add_user( u2)
        me.assert_eq_sec_flat( me._sec4db.q_users(), [ u1, u2] )

    def q_is_user( me):
        u = me.u2.name
        u1= me.u1.name
        me._sec4db.add_user( u)
        me._sec4db.add_user( u1)
        me.assert_eq_sec( names= [ u, u1] )

        me.assert_eq( me._sec4db.q_is_user( u1), True)
        me.assert_eq( me._sec4db.q_is_user( u),  True)
        me.assert_eq( me._sec4db.q_is_user( u+u1), False)

        me._sec4db.del_user( u1)
        me.assert_eq( me._sec4db.q_is_user( u1), False)
        me.assert_eq( me._sec4db.q_is_user( u),  True)

class sec4db_noautoadmin( sec4db):
    AUTOADMIN = False

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
