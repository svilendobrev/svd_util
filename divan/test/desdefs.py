#!/usr/bin/env python
# -*- coding: utf-8 -*-

from adb import *

from data.cubase import Base, js_if_doc_type
from data.views import ViewDefinition, ValidatorDefinition
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
                func = ValidatorDefinition.required + ValidatorDefinition.user_is_role +
                    '''
                    required( "type" );
                    if (oldDoc && !user_is("admin")) throw({forbidden: "%s"});
                    ''' % _error_non_admin
                )
class Mgr:
    def Proba( me, **ka):
        return Proba( me, **ka)

class Mgr( cu.Mgr, Mgr): pass
cudb.Mgr = Mgr

class desdefs( test4db, TEST):
    DBNAME = Proba.DBNAME
    u = DictAttr( name= 'u', password= 'u')
    u_url = u.name+':'+u.password

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

    def t_nonadmin( me):
        t1,t2 = me.t_valid()
        url = cudb.srv_args['url']
        ss = url.split('@',1)
        if len(ss)>1:
            ss[0] = ss[0].split('://')[0]
        else:
            ss = url.split('://')
        m2 = cudb.Mgr( url= ss[0] + '://'+me.u_url+'@'+ss[1] )
        q = m2.Proba()
        me.assert_eq_all( q.q_typ(), [ t1 ] )
        with me.assertRaises( couchdb.ForbiddenError) as cm:    #ServerError/403
            me.p._save( t1)
        me.assertTrue( Proba._error_non_admin in cm.exception.message)

if __name__ == '__main__':
    main_no_users()

# vim:ts=4:sw=4:expandtab
