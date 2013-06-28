#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

#TODO
# + permanent views     http://wiki.apache.org/couchdb/HTTP_view_API#Temporary_Views
# - update handlers     http://wiki.apache.org/couchdb/Document_Update_Handlers
# - update validators   http://wiki.apache.org/couchdb/Document_Update_Validation
# - XXX all dbs should be owned by admin by default .. i.e. default.owner-per-server ?

from svd_util import dbg
log = dbg.log_funcname.log

from svd_util.struct import DictAttr

from uuid import uuid4
def uuid(): return uuid4().hex
import time

import couchdb_hacks
from couchdb import Server, ResourceNotFound, ResourceConflict, PreconditionFailed
from couchdb import client
from views import ViewDefinition, DesignDefinition


#other special views Server.:
# .config .stats .tasks .uuids
# just server.resource.get_json()  also should give some info??


# XXX if server  -> does ping !
# XXX if db      -> does ping !
# XXX use .. is None

#dbg.Meta4log.funcwrap.really = False
#dbg.Meta4log.funcwrap.log = False

#class ErrorAlreadyExists( RuntimeError): pass
#class ErrorNotExists( RuntimeError): pass

class NOVALUE:
    'use for startkey/endkey or others where None is valid value'
    #def __bool__( me): return False ???
    pass

class Storage( object):
    def __init__( me, **kargs):
        me.server = Server( **kargs)

    def sync_all_views( me):
        'for all dbs!'
        DesignDefinition.sync_all_views( me.viewdb2db)
        for dbname in me.server:
            me.setup_if_templated( dbname= dbname)

    dbkind_by_name = DictAttr()
    dbtemplate_by_dbkind = DictAttr()   #reduce kinds

    #XXX db-kinds and templates are not real databases
    def viewdb2db( me, dbname):
        if dbname in me.dbkind_by_name: return
        if dbname in me.server: return me.server[ dbname ]
        return me.server.create( dbname)

    @classmethod
    def get_dbkind_by_name( me, dbname):
        assert None not in me.dbkind_by_name
        for kind,matcher in me.dbkind_by_name.items():
            if matcher( dbname):
                return kind
    @classmethod
    def is_templated( me, dbname):
        #log()
        kind = me.get_dbkind_by_name( dbname)
        if kind is not None:
            return me.dbtemplate_by_dbkind.get( kind, kind)

    def setup_if_templated( me, db =None, dbname =None, template =None):
        template = template or me.is_templated( dbname or db._name)
        log()
        #me.security( db= db, dbname= dbname, template=template)
        if not template: return

        if db is None: db = me.server[ dbname]
        views = DesignDefinition.designs4db.get( template)
        if views:
            DesignDefinition.sync_one_db( db, views, remove_missing =False,)
        #XXX it can only remove stuff in known designdocs.. mentioned in views

    def open( me, dbname, maycreate =False, new =False, ok_if_no_db =False, template =None):
        ''' open dont create    - maycreate=False
            open or create      - maycreate=True
            create dont open    - new=True
        '''
        #naming: see http://wiki.apache.org/couchdb/HTTP_database_API
        #log()
        server = me.server
        assert dbname

        if not new:
            try:
                return server[ dbname]
            except ResourceNotFound, e:
                if not maycreate:
                    if ok_if_no_db: return None
                    e.args = ( dbname,)
                    raise

        try:
            db = server.create( dbname)
        except Exception as e:
            emsg = str(e) + '; dbname='+dbname + ' @'+str(server)
            if isinstance( e, PreconditionFailed):
                if 'file_exists' in e.message:
                    raise ResourceConflict( emsg)
            import traceback
            traceback.print_exc()
            raise RuntimeError( emsg)

        db._just_created = True
        me.setup_if_templated( db= db, template= template)
        return db

    def destroy( me, dbname ='', db =None ):
        if not dbname: dbname = db._name
        del me.server[ dbname]

    #XXX include_docs=True saves index.space but is extra lookup per row and
    #   a race cond - to avoid it, emit {"_rev": doc._rev} instead of null.
    #   still, the result can be already deleted - and will have _deleted=true

    @classmethod
    def q_doc( me, db,
            view,               #a viewdef, or if str, either viewname or map_fun (for tmp)
            tmp         =False,
            no_obj      =False,
            only_keys   =False,
            only_ids    =False,
            raw         =False,
            prn         =False,
            **ka ):

        ka = dict( (k,v) for k,v in ka.items() if v is not NOVALUE)

        include_docs = ka.get( 'include_docs')
        if only_keys:
            assert not include_docs
            #ka[ 'include_docs'] = False

        if ka.get( 'descending'):   #swap meaning
            s = ka.pop( 'startkey', NOVALUE)
            e = ka.pop( 'endkey', NOVALUE)
            if s is not NOVALUE: ka[ 'endkey'] = s
            if e is not NOVALUE: ka[ 'startkey'] = e

        if isinstance( view, basestring):
            if tmp or ' ' in view:
                r = ViewDefinition( '', map_fun= view, **ka ).query( db, tmp= True, )
            else:
                r = db.view( view, **ka)
        else:
            r = view.query( db, tmp= tmp, **ka)
            include_docs = include_docs or view.defaults.get( 'include_docs')
        avalue = only_keys and 'key' or only_ids and 'id' or include_docs and 'doc' or 'value'
        no_obj = no_obj or only_keys or only_ids
        for v in r:
            if prn: print( prn, v)
            if not raw: v = v[ avalue]
            yield v if no_obj else DictAttr( v)

    @classmethod
    def all_docs( me, db, raw =False, all =False, **ka):
        if raw: r = db.view( '_all_docs', include_docs= True, **ka)
        else: r = me.q_doc( db= db, view= '_all_docs', include_docs= True, **ka)
        if all: return r
        return [ x for x in r if x['_id'][0]!='_' ]


    def list( me):
        return iter( me.server)

    def dump( me, dbname =None):
        s = me.server
        for name in dbname and [ dbname ] or s:
            if name[0]=='_' and name != dbname: continue
            db = s[ name]
            print( db)
            print( db.info() )
            for doc_id in db:
                print( db.get( doc_id))

    class Replica:
        def __init__( me, storage):
            me.storage = storage
            me.db = storage.server[ '_replicator']

        @staticmethod
        def is_repl_ok( doc):
            return doc.get( '_replication_state') != 'error' #==triggered ??

        def all_same_source_target( me): return me._all_same_source_target( me.local, me.remote)
        def _all_same_source_target( me, local, remote):
            for dir,startkey in dict( push= [ local, remote], pull= [ remote, local] ).items():
                for doc in me.storage.q_doc( me.db,
                            ''' if (doc.source && doc.target) emit( [doc.source, doc.target], null ); ''',
                        #only_ids = True,
                        startkey = startkey,
                        endkey   = startkey + [1],
                        include_docs =True,
                        ):
                    if not me.is_repl_ok( doc): continue
                    yield dir, doc._id, startkey

        def all_for_local( me, **ka): return me._all_for_local( me.local, **ka)
        def _all_for_local( me, local, **ka):
            return me.storage.q_doc( me.db, '''
                            if (doc.source && doc.target) {
                                emit( doc.source, null );
                                emit( doc.target, null );
                            } '''
                            ,
                        startkey = local,
                        endkey   = local + ':',
                        **ka
                        )
        def all( me):
            for k in me.db:
                if k[0] != '_': yield k

        def delete( me, k):
            del me.db[k]

        def init( me, dbname, remote, local =None, userpasw =None):
            #XXX TODO use cookies - obtain from /session
            # e.g. headers= dict( cookie= "AuthSession=foo")

            if '//' in dbname:  #full addresses
                local = dbname
            else:
                remote = '/'.join( a.rstrip('/') for a in [remote, dbname] if a)
                if userpasw and not local: local = me.storage.server.resource.url
                local = '/'.join( a.rstrip('/') for a in [local, dbname] if a)

            me.remote_adr = user2url( remote)
            me.local_adr  = user2url( local)
            if userpasw:
                remote= user2url( remote, userpasw)
                local = user2url( local,  userpasw)
            me.remote= remote
            me.local = local

        def is_needed( me):
            available = {}
            if 'same local but remote_adr only':
                for doc in me.all_for_local( include_docs= True):
                    if not me.is_repl_ok( doc): continue
                    if doc.source == me.local:
                        if user2url( doc.target) == me.remote_adr: available['push'] = 1
                    else:
                        assert doc.target == me.local
                        if user2url( doc.source) == me.remote_adr: available['pull'] = 1
            else:
                for dir,k,fromto in me.all_same_source_target():
                    available[ dir] = k

            if not available: return True
            elif 'pull' not in available: return 'pull'
            elif 'push' not in available: return 'push'
            return False

        def pull( me, **ka):
            return me.storage.server.replicate( me.remote, me.local, **ka)
        def push( me, **ka):
            return me.storage.server.replicate( me.local, me.remote, **ka)


    def _Replicator( me, dbname, remote, local =None, userpasw =None, ):    #if set, apply to both remote+local
        rr = me.Replica( me)
        rr.init( dbname, remote= remote, local= local, userpasw= userpasw)
        return rr

    def replicate( me, dbname, remote, local =None,
            continuous  =True,
            stop_local  =True,      #cancel all for same local
            stop_all    =False,     #cancel all
            repl        =True,      #start repl
            only_if_missing =False, #do nothing if same repl exists else start what's missing
            userpasw    =None,      #if set, apply to both remote+local
            replicator  =None,
            opts    = {},
            ):

        opts = dict( opts, continuous= continuous,)
        #if headers: opts['headers'] = headers
        #if cancel: opts['cancel'] = True XXX OLDSTYLE  /_replicate/

        rr = replicator or me._Replicator( dbname, remote= remote, local= local, userpasw= userpasw)

        repl = bool( repl)      #avoid trouble

        if repl and only_if_missing:
            repl = rr.is_needed()
            if not repl:
                print( 'replicate-available', rr.local, rr.remote)
                return

        if stop_all:
            for k in rr.all():
                print( ' >replicate-stop', k)
                rr.delete( k)
        elif stop_local:
            if 0:
                #cancel all same source,target
                for dir,k,fromto in rr.all_same_source_target():
                    print( ' >replicate-cancel', k, fromto)
                    rr.delete( k)
            else:
                #cancel all to/from same local
                for k in rr.all_for_local( only_ids= True):
                    print( ' >replicate-cancel', k, local)
                    rr.delete( k)

        if repl:
            print( 'replicate', repl is not True and repl or '', local, remote, opts)
            pull = repl != 'push' and rr.pull( **opts)
            push = repl != 'pull' and rr.push( **opts)
            print( ' -', pull, push)
            return pull, push

    def changes( me, dbname, **ka):
        ka.setdefault( 'include_docs', True)
        ka.setdefault( 'feed', 'continuous')
        ka.setdefault( 'heartbeat', 30000  )  #XXX default timeout in .ini is 60000ms == default heartbeat
        try:
            db = me.server[ dbname]
        except ResourceNotFound:
            yield ResourceNotFound
            return
        if ka['feed'] == 'continuous':
            for c in db.changes( **ka):
                yield c
        else:
            r = db.changes( **ka)
            for c in r.pop('results'):
                yield c
            yield r #['last_seq']



dbg.Meta4log.funcwrap.pfx = '\n '

class Base( object):
    __metaclass__ = dbg.Meta4log
    LOG_PFXS = 'q_ '+ 0*' _open _connect'
    LOG_PFXS_EXCL = '__'

    db = None

    def _uuid( me): return uuid()

    @classmethod
    def _message_copy( me, doc, skip_fields ='_rev _id'.split() ):
        m = dict( doc)
        for f in skip_fields: m.pop( f, None)
        return m
    @classmethod
    def _message_copy_keep_id( me, doc):
        return me._message_copy( doc, skip_fields= ('_rev',) )

    def _init4DBNAME( me, storage, **ka):
        me._open( storage, dbname= me.DBNAME, **ka)

    def _open( me, storage =None, db= None, **ka):
        me.storage = storage
        if db is not None:
            me.db = db
        else:
            db = me.db = storage.open( template= me._KIND, **ka)
        return db
    def _destroy( me ):
        me.storage.destroy( db= me.db)

    def _q_doc( me, *a,**k):  return me.storage.q_doc( me.db, *a,**k)
    def _all_docs( me, **ka): return me.storage.all_docs( me.db, **ka)

    @property
    def dbname( me): return me.db._name

    _KIND = None
    def setup_if_templated( me):
        me.storage.setup_if_templated( db= me.db, template= me._KIND)

    def _delete( me, id, ok_if_missing =False):
        assert isinstance( id, basestring)
        try:
            del me.db[ id]  #dontconflict, del last one
        except ResourceNotFound, e:
            if not ok_if_missing:
                e.args = ( id,)
                raise

    def get( me, id, ok_if_missing =False):
        assert isinstance( id, basestring)
        try:
            return DictAttr( me.db[ id])
        except ResourceNotFound, e:
            if not ok_if_missing:
                e.args = ( id,)
                raise

    def has( me, id):
        assert isinstance( id, basestring)
        return id in me.db

    def _save( me, d):
        'does update d'
        me.db.save( d)
        return d
    def _save_and_repeat_if_gone( me, d):
        me.db.save( d)
        #XXX repeat for the COUCHDB-1415 defect - for recreating same-id docs
        check = me.get( d['_id'], ok_if_missing= True)
        if not check: me.db.save( d)
        return d

    def last_seq( me):
        return me.db.info()[ 'update_seq'] #committed_

    @staticmethod
    def _update_if_not_None( dct, **ka):
        for k,v in ka.items():
            if v is not None:
                dct[k] = v
        return dct

    def _set_field( me, u, field, value, save= True):
        if u.get( field) == value: return
        u[ field] = value
        if save: me.db.save( u)
    def _del_field( me, u, field, default =None, save= True):
        if field not in u: return default
        r = u.pop( field)
        if save: me.db.save( u)
        return r
    def _add_to_field( me, u, field, value, save= True):
        if add_to_field( u, field, value) is None: return
        if save: me.db.save( u)
    def _del_from_field( me, u, field, value, save= True):
        if del_from_field( u, field, value) is None: return
        if save: me.db.save( u)

    def _changes( me, **ka):
        return me.storage.changes( me.dbname, **ka)

# add_to_field and del_from_field are made to:
#   - allow non-list single value (treated as list of 1 element - the value)
#   - dont change if no need
#   - None is a possible value
#   - mostly stable/repeatable add(del(add)))

def add_to_field( u, field, value):
    ''' if no field, assign; else if not a list, convert to list; append if not already there
        #.    + None -> None
        .    + x    -> x
        #None + None -> None
        #None + x    -> [None,x]
        #a    + None -> [a,None]
        a    + a -> a
        a    + x -> [a,x]
        [a]  + a -> [a]
        [a]  + x -> [a,x]
    '''
    if field not in u:
        v = value
    else:
        v = u.get( field)
        if isinstance( v, tuple): v = list(v)
        if not isinstance( v, list): v = [v]
        if value in v: return
        v.append( value)
    u[ field] = v
    return u

def del_from_field( u, field, value, dont_empty =False):
    ''' if not a list, convert to list; delete value if in list; delete field if nothing left
        #.    - None -> .
        .    - x    -> .
        #None - None -> .
        #None - x    -> None
        #a    - None -> a
        a    - a -> .
        a    - x -> a
        [a]  - a -> .
        [a]  - x -> [a]
    '''
    if field not in u: return
    v = u.get( field)
    if isinstance( v, tuple): v = list(v)
    if not isinstance( v, list): v = [v]
    if value not in v: return
    if dont_empty and len(v)<=1: return  #separate non-destructive check
    v.remove( value)
    if not v:
        u.pop( field)
    else:
        u[ field] = v
    return u

def js_if_doc_type( typ):
    return ' if (doc.type && doc.type == "' + typ + '") '

class Pfx:
    def __init__( me, pfx): me.pfx = pfx
    def a2id( me, a):
        return me.pfx+a
        if not a.startswith( me.pfx): a = me.pfx+a
        return a
    def id2a( me, id):
        assert id.startswith( me.pfx), id
        return id[ len(me.pfx):]



def user2url( url, userpasw =None):
    'replace/insert/strip userpasw in url'
    from urlparse import urlparse, urlunparse
    u = urlparse( url)._asdict()
    u['netloc'] = '@'.join( f for f in [ userpasw, u['netloc'].split('@')[-1]] if f)
    url = urlunparse( u.values())
    return url



def optz_str():
    return dict( default= 'http://localhost:5984', help= 'couchdb server url' )

def optz_url_usr( optz):
    optz.str( 'couchdb', **optz_str())
    optz.str( 'userpsw', help= 'user:psw for http; override those in url')

def optz_url_usr_fix( optz):
    if optz.userpsw:
        optz.couchdb = user2url( optz.couchdb, optz.userpsw)
    print( '.. url=', optz.couchdb)

# vim:ts=4:sw=4:expandtab
