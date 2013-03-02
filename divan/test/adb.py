#!/usr/bin/env python
# -*- coding: utf-8 -*-

from svd_util.struct import DictAttr
import unittest

import types as _types
from traceback import print_exc

class Missing: pass

def hasher( x):
    if isinstance( x,list): return tuple( sorted( hasher(i) for i in x))
    if isinstance( x,dict): return tuple( sorted( (hasher(k),hasher(v)) for k,v in x.items()))
    return x

class adicty( dict):
    def __new__( klas, *a,**k):
        if len(a)==1 and not isinstance( a[0], (dict, _types.GeneratorType) ): return a[0]
        r = dict.__new__( klas, *a,**k)
        #for k,v in r.items():
        #    if isinstance( v, dict): v.__hash__ = klas.__hash__.im_func
        return r
    def __hash__( me):
        return hash( hasher(me))#tuple( (k,hasher(v) ) for k,v in sorted( me.items())))

from operator import getitem
def dicty( x, asof, getattr= lambda x,k,*df: x.get(k,*df) ):
    if not isinstance( x, dict) or not isinstance( asof, dict): return x
    return adicty( (k, getattr( x, k, Missing)) for k in asof)

def uni2str4kv( x):
    return [ dict(
                (str(k),str(v) if isinstance(v,basestring) else v)
                    for k,v in a.items())
                for a in x]
from data import cu

from data.couchdb_hacks import put_json_always
from couchdb import ResourceConflict, ResourceNotFound

#silent
cu.Base.__metaclass__.funcwrap.log = False
cu.dbg.log_funcname.do_log = False
from data.views import DesignDefinition
DesignDefinition.do_print = None

######

def pfx_dbname( dbname, pfx ='test' ):
    return pfx + '_' + dbname


class cudb( object):
    'change users database'
    Mgr = cu.Mgr
    srv_args = dict( url= cu.optz_str()[ 'default'] )

    _org_userdbname = cu.Users.DBNAME
    USERDBNAME = pfx_dbname( _org_userdbname)
    cu.Users.DBNAME = USERDBNAME
    cur_userdbname = _org_userdbname
    org_userdbname = _org_userdbname
    if _org_userdbname in DesignDefinition.designs4db:
        DesignDefinition.designs4db[ USERDBNAME ] = DesignDefinition.designs4db[ _org_userdbname]

    @classmethod
    def setup_extra( me): pass

    @classmethod
    def setup_mgr( me):
        me.mgr = me.Mgr( **me.srv_args)

    @classmethod
    def setup( me):
        me.setup_mgr()
        s = me.mgr.server
        USERDBNAME = me.USERDBNAME
        if me.cur_userdbname == USERDBNAME: return

        #print 1111111111, USERDBNAME
        #~HACK
        me.scfg = s.resource( *'_config/couch_httpd_auth/authentication_db'.split('/') )
        if USERDBNAME in s: me.unsetup()
        try:
            me.mgr.open( USERDBNAME, new=True) #emplate= me._org_userdbname)
            #s.create( USERDBNAME )
            me.org_userdbname = put_json_always( me.scfg, body= USERDBNAME )[2]
            me.cur_userdbname = USERDBNAME
            #print 323232, me.org_userdbname, me.cur_userdbname

            me.setup_extra()
        except:
            me.unsetup()
            raise

    @classmethod
    def unsetup( me):
        #print 333333, me.org_userdbname
        if 1: #me.cur_userdbname != me._org_userdbname:
            put_json_always( me.scfg, body= me._org_userdbname)
            me.cur_userdbname = me._org_userdbname
        s = me.mgr.server
        try:
            del s[ me.USERDBNAME ]
        except ResourceNotFound:
            pass


def strdict( d, exclude =['me']):
    return '\n'.join( ('%s=%r' % (k,v)) for k,v in d.items() if k not in exclude)
def strlist( d):
    return '\n'.join( str(r) for r in d)

class test4me( object):
    _NOMETA = 1
    class __metaclass__( type):
        def __new__( meta, name, bases, dict_):
            pfxs = '_ assert setup tear unsetup'.split()
            def is_pfx( name):
                name = name.lower()
                for p in pfxs:
                    if name.startswith( p): return False
                return True
            if '_NOMETA' not in dict_:
                dict_.update( ('test_'+k, v)
                    for k,v in dict_.items()
                    if (isinstance( v, ( _types.FunctionType, _types.GeneratorType, _types.MethodType, ))
                        and is_pfx( k))
                    )
            return type.__new__( meta, name, bases, dict_)

    #    me.maxDiff = None

    def setUp( me):
        me._setup()
        return me.setup()
    def _setup( me): pass
    def setup( me): pass
    def tearDown( me):
        me.unsetup()
        me._unsetup()
    def unsetup( me): pass
    def _unsetup( me): pass

    def assert_eq( me, *a,**k): return me.assertEquals( *a,**k)
    def assert_eq_all( me, result, expect, op =list, asof =None):
        result = list( result)
        expect = list( expect)
        #me.assert_eq( len( result), len( expect) )
        if asof is zip:
            rr = op( dicty( r, e) for r,e in zip( result, expect) )
            exp = op( adicty( d) for d in expect )
        else:
            if not asof and expect:
                asof = expect[0]
                exp = op( dicty( d, asof) for d in expect)
            else:
                exp = op( dicty( d, asof) for d in expect)
            rr = op( dicty( d, asof) for d in result)
        #print 7777777777, asof
        #print 77777777772, strlist( rr)
        #print 77777777773, strlist( exp)
        try:
            me.assert_eq( rr, exp )
        except:
            print 'result:'
            print '', strlist( result)
            print 'expect:'
            print '', strlist( expect)
            print 'resultX:'
            print '', strlist( rr)
            print 'expectX:'
            print '', strlist( exp)
            raise

    def assert_eq_set( me, *a,**ka):
        return me.assert_eq_all( op= set, *a,**ka)
    def assert_eq_sorted( me, *a,**ka):
        return me.assert_eq_all( op= sorted, *a,**ka)
    def assert_eq_len( me, result, lexpect):
        me.assert_eq( len( result), lexpect )
    def assert_eq_1( me, result, expect, **ka):
        return me.assert_eq_all( [ result ], [ expect ], **ka)

class test4db( test4me):
    _NOMETA = 1
    @property
    def mgr( me): return cudb.mgr

    def unsetup_db( me, quiet =False):
        try:
            #me.map._destroy()
            me.mgr.destroy( dbname= me.DBNAME)
        except ResourceNotFound:
            if not quiet: print_exc()


TEST = unittest.TestCase
class NTEST: pass

def main( users =True, db =True ):
    import sys
    try:
        i = sys.argv.index( '--url')
    except ValueError: pass
    else:
        x = sys.argv.pop(i)  #--
        x = sys.argv.pop(i)  #value
        cudb.srv_args.update( url=x)

    try:
        sys.argv.remove( '--nousers')
        users = False
    except ValueError: pass

    if users and db:
        class TestProgram( unittest.TestProgram):
            def runTests( me):
                me.exit = False
                cudb.setup()
                try:
                    unittest.TestProgram.runTests( me)
                finally:
                    cudb.unsetup()
                raise SystemExit( not me.result.wasSuccessful())
        TestProgram( exit= False, verbosity =2)

    else:
        if db: cudb.setup_mgr()
        unittest.TestProgram( verbosity =2)

def main_no_users(): main( users =False, db =True )
def main_no_db(): main( db =False)

# vim:ts=4:sw=4:expandtab
