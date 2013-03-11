#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cubase import *

# XXX if server  -> does ping !
# XXX if db      -> does ping !
# XXX use .. is None

import hashlib

class Users( Base):
    LOG_PFXS = 'user_'

    PFX4name = 'org.couchdb.user:'
    @classmethod
    def _id( me, name, id =None):
        assert (not name) != (not id)
        if id: return id
        if name.startswith( me.PFX4name): return name
        return me.PFX4name + name

    DBNAME = '_users'
    _KIND = DBNAME
    TYPE = 'user'

    def __init__( me, storage):
        me._open( storage, dbname= me.DBNAME)
        #me.setup_if_templated()

    @classmethod
    def match_password( me, user, password):
        h = hashlib.sha1()
        h.update( password)
        h.update( user.salt)
        return h.hexdigest() == user.password_sha

    def add_user( me, name, password, **ka):
        if not name: name = 'uz' + me._uuid()
        doc = me._update_if_not_None( {}, **ka)
        #avoid overriding these
        doc.update( type= me.TYPE,
            name    = name,
            _id     = me._id( name),
            password= password,
            roles   = [],
        )
        me.db.save( doc)
        return name

    def del_user( me, name =None, id= None):
        id = me._id( name, id)
        me._delete( id, ok_if_missing= True)

    def q_is_user( me, name =None, id= None):
        id = me._id( name, id)
        return id in me.db
    def q_user( me, name =None, id= None, **ka):
        id = me._id( name, id)
        return me.get( id, **ka)

    def q_users( me):
        return [ DictAttr( u['doc'])
            for u in me.db.view( '_all_docs', include_docs= True)
            if u.key.startswith( me.PFX4name)
            #if u.key[0]!='_'
            ]

    def set_field( me, username, field, value):
        u = me.db[ me._id( name= username) ]
        me._set_field( u, field, value)
    def del_field( me, username, field, default =None):
        u = me.db[ me._id( name= username) ]
        return me._del_field( u, field, default)
    def add_to_field( me, username, field, value):
        u = me.db[ me._id( name= username) ]
        me._add_to_field( u, field, value)
    def del_from_field( me, username, field, value):
        u = me.db[ me._id( name= username) ]
        me._del_from_field( u, field, value)

    _auths = 'password_sha salt auth password'.split()
    def disable_user( me,  username):
        u = me.db[ me._id( name= username) ]
        for p in me._auths:
            u.pop( p, None)
        me.db.save( u)


class Sec4db( Base):
    LOG_PFXS = '*'
    _security_name = '_security'
    sec = None

    def __init__( me, db =None, storage =None, dbname =None, ok_if_no_db =False):
        db = me._open( storage, dbname= dbname, db= db, ok_if_no_db= ok_if_no_db)
        if db is not None:
            me._dbname = me.dbname
            #_security obj has no id..
            me.sec = db[ me._security_name]
        else:
            me._dbname = str(dbname)

    def _save( me):
        status, headers, data = me.db.resource.put_json( me._security_name, body= me.sec)

    def add_user( me, username, overwrite =False):
        rs = me.sec.setdefault( 'readers', {})
        ns = rs.setdefault( 'names', [])
        if overwrite: ns[:] = []
        elif username in ns: return     #ok if already there
        ns.append( username)
        me._save()

    def del_user( me, username, at_least_admin ='admin'):
        if me.db is None: return        #ok if missing
        rs = me.sec.get( 'readers')
        if not rs and not at_least_admin: return
        ns = rs.get( 'names', ())
        if not ns and not at_least_admin: return
        while username in ns: ns.remove( username)
        if at_least_admin and not ns:
            rs = me.sec.setdefault( 'readers', {})
            rs[ 'names'] = [ at_least_admin ]
            #ns.append( at_least_admin )
        #print 22222222, ns, me.sec
        me._save()

    def q_users( me):
        rs = me.sec.get( 'readers')
        return rs and rs.get( 'names' ) or ()

    def q_is_user( me, username ):
        return username in me.q_users()

    @classmethod
    def q_db_by_user( klas, databases, username):
        return [ db for db in databases
                    if klas( db= db ).q_is_user( username )
                ]

    def __str__( me): return me.__class__.__name__ + '/' + me._dbname

class Channel4user( Base):
    LOG_PFXS = '*'

    PREFIX = 'cz'
    @classmethod
    def _cc_name( me, user): return me.PREFIX + user
    @classmethod
    def _user_from_name( me, ccname):
        assert ccname.startswith( me.PREFIX)
        return ccname[ len( me.PREFIX):]


    def q_user( me):
        uu = me.storage.Sec4db( db= me.db ).q_users()
        assert len(uu) == 1, uu
        return uu[0]

    _KIND = 'cc'

    USER_FIELD = 'control_channel'

    #XXX lazy - for create/del
    def __init__( me, storage, username ):
        me.username = username
        me.storage = storage

    def __repr__( me):
        return me.__class__.__name__ + '/' + me.username

    def _open( me, **ka):
        return Base._open( me, me.storage, dbname= me._cc_name( me.username), **ka)

    def __str__( me): return me.__class__.__name__ + '/' + me.username

    _db = None
    def _db_get( me):
        db = me._db
        if db is None: return me._open()# ok_if_no_db =True)
        return db
    def _db_set( me, v): me._db = v
    db = property( _db_get, _db_set)

    def create( me, update_user =True, update_sec =True, new= True, empty_sec =False, **ka):
        #if new:
        #    assert me.db is None, me.db
        me._open( maycreate= True, new= new, **ka)
        #variants: XXX
        # has users and auth:   +update_user +update_sec -empty_sec
        # has users, no auth:   +update_user +update_sec +empty_sec
        # no users, no auth:    -update_user +update_sec +empty_sec
        if update_sec:
            if not empty_sec:
                me.storage.Sec4db( db= me.db ).add_user( me.username)
            else:
                me.storage.Sec4db( db= me.db ).del_user( me.username, at_least_admin =None)
        if update_user:
            if isinstance( update_user, dict):
                assert update_user.get( 'name') == me.username
                me.storage.Users()._set_field( update_user, me.USER_FIELD, me.db._name)
            else:
                me.storage.Users().set_field( me.username, me.USER_FIELD, me.db._name)

    def disable( me, update_user =False):
        #make inaccessible
        me.storage.Sec4db( db= me.db ).del_user( me.username )#, at_least_admin= 'admin')
        if update_user:
            me.storage.Users().del_field( me.username, me.USER_FIELD)

    def destroy( me, update_user =True):
        try: me._destroy()
        except ResourceNotFound: pass
        if update_user:
            me.storage.Users().del_field( me.username, me.USER_FIELD)

    if 0:
        def save( me, doc):
            me.db.save( doc)

def itemset_mixin( type, dbkind):

    class itemset_mixin( object):
        TYPE = type

        def add_item( me, item):
            #XXX rename = add_discussion
            #me._open( maycreate= True)  #may autocreate if valid user
            try:
                me.db[ item] = dict( type= me.TYPE)
            except ResourceConflict: pass           #ok if already there

        def del_item( me, item):
            if me.db is None:
                me._open( ok_if_no_db =True)
            if me.db is not None:   #ok if no channel
                me._delete( item, ok_if_missing= True)

        def q_has_item( me, item):
            return me.db is not None and item in me.db

        def q_items( me, view =ViewDefinition( 'itemset/'+type,
                db= dbkind,
                map_fun = js_if_doc_type( type ) + 'emit( null, null ); ',
                ) ):
            r = me._q_doc( view, only_ids= True,)
            return list( r)
    itemset_mixin.__name__ += '4'+type
    return itemset_mixin

Storage.dbkind_by_name[ Channel4user._KIND ] = lambda dbname: dbname.startswith( Channel4user.PREFIX)

class Channel4user_mixin:
    _KIND = Channel4user._KIND

    def _open( me, channel4user, **ka_ignore):
        assert channel4user is not None
        me.channel4user = channel4user
        db = me.db = me.channel4user.db
        me.storage = me.channel4user.storage
        return db

    @staticmethod
    def ViewDefinition( name, db= _KIND, **ka):
        return ViewDefinition( name, db= db, **ka )

    def _init4owner( me, owner =None, **ka):   #??
        me.owner = owner
        me._open( **ka)

    @staticmethod
    def _factory( factory, channel4user_factory, owner =None, channel4user =None):
        if channel4user is None:
            assert owner or channel4user
            channel4user = channel4user_factory( owner)
        else:
            assert not owner
            owner = channel4user.username
        return factory( channel4user= channel4user, owner= owner)


class Mgr( Storage):
    if 0:
        def discus_walker( me):
            return [
                me.Discu( 'bzzz', dbname, server= me.server )
                for dbname in me.server
                if dbname[0] != '_'
                ]
        def q_discus_by_user( me, user, **ka):
            return me._Discu.q_discus_by_user( user, me.discus_walker(), **ka )
    def __repr__( me):
        return me.__class__.__name__+'/'+str( me.server)

    _Users = Users
    _users = None
    def Users( me):
        u = me._users
        if u is None:
            u = me._users = me._Users( me)
        return u

    _Channel4user = Channel4user
    def Channel4user( me, username): return me._Channel4user( me, username)

    _Sec4db = Sec4db
    def Sec4db( me, **ka): return me._Sec4db( storage= me, **ka)



class cmd:
    all_optz = []
    @classmethod
    def optz( me, optz):
        optz_url_usr( optz)
        optz.str( 'method')
        optz.bool( 'api',       help= 'list api methods')
        optz.bool( 'sync_views', help = 'sync before doing other stuff')
        optz.str( 'user',     default= 'me', help= 'user name for methods [%defaults]')
        optz.bool( 'users',     help= 'Users api')
        optz.str( 'sec4db',     help= 'db id to use for sec4db')
        for o in me.all_optz:
            o( optz)
        optz, argz = optz.get()
        optz_url_usr_fix( optz)
        return optz,argz

    all_klasi = [ Users, Channel4user, Sec4db ]
    @classmethod
    def cmd( me, optz):
        if optz.api:
            import inspect
            from svd_util.attr import inspect_methods
            for klas in me.all_klasi:
                methods = inspect_methods( klas)
                for kl,mm in sorted( methods.items(), key= lambda kv: kv[0].__name__ ):
                    for name, m in mm.items():
                        argspec = inspect.getargspec( m)
                        print kl, name, inspect.formatargspec( argspec[0][1:], *argspec[1:])
        #elif optz.dumpdbs:      pprint( EVENTER.adb )
        #elif optz.dumpdb:       pprint( EVENTER.adb[ optz.dumpdb])
        else: return
        raise SystemExit, 1

    all_makers = []
    @classmethod
    def go( me, Mgr, optz, argz, obj_maker =None, **ka):
        me.cmd( optz)

        mgr = Mgr( url= optz.couchdb, **ka)
        if optz.sync_views: mgr.sync_all_views()
        c = None
        if obj_maker:
            c = obj_maker( mgr, optz, argz)
        if c is None:
            for go in me.all_makers:
                c = go( mgr, optz) # or None
                if c: break
        if c is None:
            if optz.users:      c = mgr.Users()
            elif optz.sec4db:   c = mgr.Sec4db( dbname= sec4db)
            elif optz.user:     c = mgr.Channel4user( username= optz.user)

        if optz.method:
            tx = {  'False': False,
                    'None':  None,
                    'True':  True,
                    }
            d = dict( (k,tx.get(v,v)) for k,v in [ a.split( '=', 1) for a in argz] )
            method = getattr( c, optz.method)
            print method
            import pprint
            import types
            r = method( **d)
            if isinstance( r, types.GeneratorType): r = list(r)
            pprint.pprint( r)
        return c

    @classmethod
    def append( me, optz =None, klas =None, maker =None):
        if optz: me.all_optz.append( optz)
        if klas: me.all_klasi.append( klas)
        if maker: me.all_makers.append( maker)
'''
storage
    userMgr()
        +views
    Sec4db( db, dbname)
        +views
    Channel4user( username)
        +views

    discussionReader( discid)
        +views
    discussionWriter( discid, person)
        #make if discid=None
'''

if __name__ == '__main__':
    from svd_util import optz
    optz,argz = cmd.optz( optz)
    cmd.go( Mgr, optz, argz)

# vim:ts=4:sw=4:expandtab
