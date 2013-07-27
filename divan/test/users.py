#!/usr/bin/env python
# -*- coding: utf-8 -*-
from data.divan import cu
from data import cuemail2user    #before import adb
class Users_email( cu.Users, cuemail2user.Users_email): pass
cu.Mgr._Users = Users_email
from adb import *

class test4db_users( test4db):

    u1 = DictAttr(
            #email = 'oh@thisis.my',
            name  = 'som namee',
            password = 'fryk',
            )
    u2 = DictAttr(
            #email = 'and@this.too',
            name  = 'othernam e',
            password = 'kuk',
            )
    u3 = DictAttr(
            #email = 'or@that.eh',
            name  = 'hihihe',
            password = 'dd',
            )

    @property
    def users( me): return me.mgr.Users()

    @classmethod
    def _new_user( me, **ka):
        try:
            return cudb.mgr.Users().add_user( **ka)
        except ResourceConflict:
            return 'already exists'
    @classmethod
    def _del_user( me, **ka):
        return cudb.mgr.Users().del_user( **ka)
    @classmethod
    def _all_users( me):
        return cudb.mgr.Users().q_users()

    @classmethod
    def _make_users( me):
        for n,u in enumerate( [me.u1, me.u2, me.u3], 1):
            me._new_user( **u)
        return n
    @classmethod
    def _destroy_users( me):
        for u in [me.u1, me.u2, me.u3]:
            me._del_user( name=u.name)


class t1_user( test4db_users, TEST):

    def setup( me):
        cudb.setup()
        cudb.mgr.Users().setup_if_templated()   #XXX was inside Users()..
    def unsetup( me):
        cudb.unsetup()

    def assert_created_ok( me, r):
        #me.assert_eq( r, None )
        pass
    def assert_eq_all_users( me, expect):
        return me.assert_eq_set( me._all_users(), expect)

    def create( me):
        me.assert_eq_all_users( [] )
        u = me.u1

        r = me._new_user( **u)

        me.assert_created_ok( r)
        me.assert_eq_all_users( [ u ])
        return u

    def create_same__fails( me):
        u = me.create()

        r = me._new_user( **u)
        me.assert_eq( r, 'already exists')

        me.assert_eq_all_users( [ u ])

    #new_user_same_name_diff_email_ok

    def create_2( me):
        me.create()

        r = me._new_user( **me.u2)

        me.assert_created_ok( r)
        me.assert_eq_all_users( [ me.u1, me.u2 ] )

    def delete( me):
        u = me.create()

        r = me._del_user( name= u.name)

        me.assert_eq( r, None )
        me.assert_eq_all_users( [] )

    def q_user( me):
        u = me.create()

        me.assert_eq( me.users.q_is_user( u.name), True)
        me.assert_eq( me.users.q_is_user( u.name+'1'), False)

        me.assert_eq_1( me.users.q_user( u.name), u )
        me.assert_eq_all_users( [ u ] )

    def set_field( me):
        u = me.create()

        me.users.set_field( u.name, 'somefiel', 'someval')
        ru = me.users.q_user( u.name)
        me.assert_eq_1( ru, DictAttr( u, somefiel='someval') )

        me.users.del_field( u.name, 'somefiel')
        ru = me.users.q_user( u.name)
        me.assert_eq_1( ru, u )
        me.assert_eq_all_users( [ u ] )
if 0:
    def q_user_by_email( me):
        me._make_users()
        u = me.u2
        r = me.users.q_user_by_email( u.email)
        me.assert_eq_1( r, u )

    def add_del_email2( me):
        u = me.create()

        em = u.email
        ex = em+'x'
        me.assert_eq_all_users( [ dict(u, email= em) ])

        me.users.add_to_field( u.name, 'email', ex)
        me.assert_eq_all_users( [ dict(u, email= [em, ex]) ])

        me.users.add_to_field( u.name, 'email', em) #repeat
        me.assert_eq_all_users( [ dict(u, email= [em, ex]) ])

        me.users.del_from_field( u.name, 'email', ex)
        me.assert_eq_all_users( [ dict(u, email= [em]) ])

        me.users.add_to_field( u.name, 'email', ex)
        me.assert_eq_all_users( [ dict(u, email= [em, ex]) ])

        me.users.del_from_field( u.name, 'email', em)
        me.assert_eq_all_users( [ dict(u, email= [ex]) ])
        return u,ex

    def no_del_last_email1( me):
        u = me.create()
        em = u.email
        me.users.del_from_field( u.name, 'email', em)
        #me.assert_eq_all_users( [ dict(u, email= Missing) ])
        me.assert_eq_all_users( [ dict(u, email= em) ])

    def no_del_last_email2( me):
        u,ex = me.add_del_email2()
        me.users.del_from_field( u.name, 'email', ex)   #should fail
        me.assert_eq_all_users( [ dict(u, email= [ex]) ])

if __name__ == '__main__':
    main()

# vim:ts=4:sw=4:expandtab
