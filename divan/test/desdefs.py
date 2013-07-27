#!/usr/bin/env python
# -*- coding: utf-8 -*-

from adb import *

from svd_util.divan.cubase import Base, js_if_doc_type, user2url
from svd_util.divan.views import ViewDefinition, ValidatorDefinition
import couchdb

class Proba( Base):
    DBNAME = 'pr'
    _KIND = DBNAME
    __init__ = Base._init4DBNAME

    def q_typ( me, view = ViewDefinition( 'proba/q1', dbname= DBNAME,
                map_fun = js_if_doc_type( 'typ' ) + 'emit( null, %(DOC)s ); ',
                include_docs= True
                ), **ka):
        r = me._q_doc( view, **ka)
        r = list( r)
        return r
    _error_non_admin = 'users cannot update this'
    _valider = ValidatorDefinition( 'proba/v', dbname= DBNAME,
                func = (ValidatorDefinition.tools._required +
                        ValidatorDefinition.tools._user_is_admin +
                        ValidatorDefinition.tools._forbidden + '''
                    _required( "type" );
                    if (oldDoc && !_user_is_admin()) _forbidden( "%s");
                    ''' % _error_non_admin
                ))
class Mgr:
    def Proba( me, **ka):
        return Proba( me, **ka)

class Mgr( cu.Mgr, Mgr): pass
cudb.Mgr = Mgr

class desdefs( test4db, TEST):
    DBNAME = Proba.DBNAME
    u = DictAttr( name= 'u', password= 'u')

    def setup( me):
        me.unsetup_db( quiet= True)
        try:
            me.mgr.Users().add_user( **me.u)
        except ResourceConflict: pass
        me.p = me.mgr.Proba( new= True)
        me.mgr.Sec4db( db= me.p.db ).add_user( me.u.name )

    def _all_docs( me):
        return me.p._all_docs()

    def t_valid( me):
        t1 = dict( a=1, type='typ')
        t2 = dict( a=2, type='ty2')
        me.p._save( t1)
        me.p._save( t2)
        me.assert_eq_all( me.p.q_typ(), [ t1 ] )
        me.assert_eq_set( me._all_docs(), [ t1, t2 ] )
        return t1,t2

    def t_invalid( me):
        t1 = dict( a=1, type='typ')
        t2 = dict( a=2, )
        me.p._save( t1)
        with me.assertRaises( couchdb.ForbiddenError) as cm:    #ServerError/403
            me.p._save( t2)
        #me.assert_eq( cm.exception.args[0][0], 403)
        #me.assertRaises( couchdb.ForbiddenError, me.p._save, t2)

    def t_nonadmin_vs_admin( me):
        t1,t2 = me.t_valid()
        url = cudb.srv_args['url']
        url = user2url( url, me.u.name+':'+me.u.password)
        m2 = cudb.Mgr( url= url)
        q = m2.Proba()
        me.assert_eq_all( q.q_typ(), [ t1 ] )
        x1 = dict( t1, a = 5)
        with me.assertRaises( couchdb.ForbiddenError) as cm:    #ServerError/403
            q._save( x1)
        me.assertTrue( Proba._error_non_admin in cm.exception.message)
        me.assert_eq_all( q.q_typ(), [ t1 ] )

        me.p._save( x1)
        me.assert_eq_all( q.q_typ(), [ x1 ] )

    def t_del( me):
        t1,t2 = me.t_valid()
        with me.assertRaises( couchdb.ForbiddenError) as cm:    #ServerError/403
            me.p._delete( t1['_id'])
        me.assertTrue( 'must have' in cm.exception.message)
        #me.assert_eq_set( me._all_docs(), [ t2 ] )

if __name__ == '__main__':
    main_no_users()

# vim:ts=4:sw=4:expandtab
