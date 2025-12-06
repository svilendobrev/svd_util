# -*- coding: utf-8 -*-
from __future__ import print_function

from svd_util import dbg
from svd_util.dicts import DictAttr
from svd_util.attr import subclasses
log = dbg.log_funcname.log

from couchdb import Server, ResourceNotFound, client, design
from copy import deepcopy
from itertools import groupby
from operator import attrgetter

class DesignDefinition( design.ViewDefinition):
    kind = '_view'  #_show _list _validat.. etc
    def __repr__( me):
        return '<%s %r>' % (me.__class__.__name__, '/'.join([
            '_design', me.design, me.kind, me.name
        ]))

    designs4db = {}
    def __init__( me, design_name, fname =None, **ka):
        dbname = ka.pop( 'db', None) or ka.pop( 'dbname', None)
        if dbname:
            me.designs4db.setdefault( dbname, []).append( me)
        me.dbname = dbname

        if not fname:
            if design_name:
                design_name,fname = design_name.split('/')
            else:
                design_name = fname = ''
        design.ViewDefinition.__init__( me, design_name, fname, **ka)

    def __hash__( me): return id(me)

    @staticmethod
    def all_designdocs( db):
        return db.view( '_all_docs', startkey='_design', endkey= '_designz', include_docs=True)

    _prepared = False
    def prepare( me): pass

    class kind4sync( object):
        remove_missing = False
        section = 'views'
        def _get( me, doc):
            me.missing = list( doc.get( me.section, {}).keys())
        def _set( me, doc, name, value):
            doc.setdefault( me.section, {})[ name] = value
            if name in me.missing: me.missing.remove( name)
        def _del( me, doc, name):
            for name in me.missing:
                del doc[ me.section ][ name]
        def _take( me, view):
            if not view.map_fun: return
            value = {'map': view.map_fun}
            if view.reduce_fun:
                value['reduce'] = view.reduce_fun
            return value

    @classmethod
    def sync_many( me, db, views, remove_missing =False, remove_missing_docs =False, callback =None):
        #XXX defect! h*ck! sort it stupid!
        #return design.ViewDefinition.sync_many( db, sorted( views, key= attrgetter('design')), **ka)

        views.sort( key= attrgetter('design'))

        #rework of couchdb.ViewDefinition.sync_many
        kinds = [ k() for k in [ DesignDefinition.kind4sync ] + subclasses( DesignDefinition.kind4sync) ]
        ddocs = dict( (o.id, o.doc) for o in me.all_designdocs( db))

        docs = []
        for design, views in groupby(views, key=attrgetter('design')):
            doc_id = '_design/%s' % design
            doc = ddocs.pop( doc_id, {'_id': doc_id})
            orig_doc = deepcopy(doc)
            languages = set()

            for kind in kinds:
                kind._get( doc)

            for view in views:
                if not view._prepared:
                    view.prepare()
                    view._prepared = True

                for kind in kinds:
                    value = kind._take( view)
                    if value: break
                else:
                    raise ValueError( 'unknown design-kind '+ str(view) )
                kind._set( doc, view.name, value)
                languages.add( view.language)

            for kind in kinds:
                if not kind.missing: continue
                if remove_missing or kind.remove_missing:
                    if me.do_print: print( 'remove from design-doc', db, doc['_id'], kind.section, ':', kind.missing)
                    kind._del( doc)
                if 'language' in doc:
                    languages.add( doc['language'])

            if len(languages) > 1:
                raise ValueError('Found different languages in one design document (%r)', list(languages))
            doc['language'] = list(languages)[0]

            if doc != orig_doc:
                if me.do_print: print( 'updating design-doc', db, doc['_id'])
                if callback is not None: callback(doc)
                docs.append(doc)

        if docs:
            if 'DEBUG':
                for d in docs:
                    db.save(d)
            else:
                db.update( docs)

        if remove_missing_docs and ddocs:
            for d in ddocs.values():
                if me.do_print: print( 'remove design-doc', db, d['_id'] )
                db.delete( d)

        #XXX not going to remove docs in does not know about

    do_print = True
    @classmethod
    def sync_one_db( me, db, views, remove_missing =True, remove_missing_docs =True, **ka):
        #if callback is print:
        #    callback = me.do_print and (lambda doc: print( 'updating view', db, doc['_id']) ) or None
                #import pprint
                #for l in difflib.unified_diff( *[pprint.pformat(x).splitlines(1) for x in (orig_doc, doc)]): print l

        #XXX it can only remove stuff in known designdocs.. mentioned in views
        me.sync_many( db, views,
                remove_missing = remove_missing,
                remove_missing_docs = remove_missing_docs,
                **ka
                )


    @classmethod
    def sync_all_views( me, db_opener, **ka):
        'db_opener may autocreate databases having views, return None to ignore or raise'
        print( 'sync_all_views', me.designs4db.keys() )
        #def db_opener( dbname): return server[ dbname ] if dbname in server else server.create( dbname)
        for dbname,views in me.designs4db.items():
            #print( dbname, 'sync_all_views')
            db = db_opener( dbname)
            if db is None: continue
            me.sync_one_db( db, views, **ka)

if 0:
    class kind_filter( kind_view):
        remove_missing = True
        section = 'filters'
        def _take( me, view): return view.get( 'filter')


class UpdatorDefinition( DesignDefinition):
    # http://wiki.apache.org/couchdb/Document_Update_Handlers
    class kind4sync( DesignDefinition.kind4sync):
        remove_missing = True
        section = 'updates'
        def _take( me, view): return getattr( view, 'updator', None)

    def __init__( me, name, func, **ka):
        me._args = name
        me.updator = func
        DesignDefinition.__init__( me, name, map_fun= '', **ka)
    def prepare( me):
        func = str( me.updator)
        if not func.strip().startswith( 'function('):
            func = '\n'.join( [ 'function( doc, req) {', func, '}' ])
        me.updator = func
    def clone( me, **ka):
        name = me._args
        return me.__class__( name= name, **dict( func= me.updator, **ka))
    #TODO usage
    #def put    #update
    #def post   #create

class ValidatorDefinition( DesignDefinition):
    # http://wiki.apache.org/couchdb/Document_Update_Validation
    class kind4sync( DesignDefinition.kind4sync):
        remove_missing = True
        section = 'validate_doc_update'
        def _get( me, doc):
            me.missing = doc.get( me.section) or ()
        def _set( me, doc, name, value):
            doc[ me.section ] = value
            me.missing = ()
        def _del( me, doc, name): del doc[ me.section ]
        def _take( me, view): return getattr( view, 'validator', None)

    def __init__( me, name, func, **ka):
        me._args = name
        me.validator = func
        DesignDefinition.__init__( me, name, map_fun= '', **ka)
    def prepare( me):
        func = str( me.validator)
        if not func.strip().startswith( 'function('):
            func = '\n'.join( [ 'function( newDoc, oldDoc, userCtx, secObj) {', func, '}' ])
        me.validator = func

    def clone( me, **ka):
        name = me._args
        return me.__class__( name= name, **dict( func= me.validator, **ka))

    '''
newDoc - The document to be created or used for update.
oldDoc - The current document if document id was specified in the HTTP request
userCtx - User context object, which contains three properties:
 - db - String name of database
 - name - String user name
 - roles - Array of roles to which user belongs. Currently only admin role is supported.
secObj - The security object of the database

Thrown errors must be javascript objects with a key of either "forbidden" or "unauthorized," and a value = the message:
 throw({forbidden: 'Error message here.'});
or
 throw({unauthorized: 'Error message here.'});
'''

    class tools:
        _required = '''\
    function _required( field, message /* optional */) {
        message = message || "Document must have field ." + field;
        if (!newDoc[field]) throw( {forbidden : message});
    }
'''
        _unchanged = '''\
    function _unchanged( field) {
        if (oldDoc && toJSON( oldDoc[ field]) != toJSON( newDoc[ field]))
            throw( {forbidden : "Field cannot change: " + field});
    }
'''
        _user_is_role = '''\
    function _user_is_role( role) { return userCtx.roles.indexOf(role) >= 0; }
'''
        _user_is_admin = '''\
    function _user_is_admin() { return userCtx.roles.indexOf( "_admin") >= 0; }
'''
        _forbidden    = '''\
    function _forbidden( msg) { throw( { forbidden: msg}); }
'''
        _unauthorized = '''\
    function _unauthorized( msg) { throw( { unauthorized: msg}); }
'''
        error_non_admin = 'users cannot update this'
        _forbidden_non_admin  = '''\
    function _forbidden_non_admin() { throw( { forbidden: "%(error_non_admin)s"} ); }
''' % locals()

        @staticmethod
        def forbidden( msg): return 'throw( { forbidden: "'+msg+'"});'
        @staticmethod
        def unauthorized( msg): return 'throw( { unauthorized: "'+msg+'"});'

        @classmethod
        def tools( me):
            return dict( (k,v) for k,v in me.__dict__.items()
                                if k[0]=='_' and k[:2]!='__' and isinstance( v,basestring))


class CombinedValidatorDef( ValidatorDefinition):
    '''many validation rules into one doc. usage:
    validator = CombinedValidatorDef(
                    name= 'ccvalidity/v',
                    unchanged_fields_at_upd_del = ['type'],
                    dbname= _KIND )
    and then validator.add( oldDoc=, newDoc= ..) - the things of _validators
'''
    def add( me, **ka):
        for k,vv in me._validators.items():
            v = ka.pop( k, None)
            if not v: continue
            if isinstance( v, basestring):
                v = v.strip()
                if not v: continue
                v = [v]
            vv.update( v)
        assert not ka, ka.keys()

    def __init__( me, name= 'validity/v',
                    unchanged_fields_at_upd_del = ['type'],
                    func =None,
                    **ka ):
        ValidatorDefinition.__init__( me, name= name, func= func, **ka)
        me._validators = DictAttr(
            oldDoc  = set(),
            newDoc  = set(),
            tools   = set(),
            unchanged_fields_at_upd_del = set( unchanged_fields_at_upd_del)
            )

    def prepare( me):   #lazy at usage
        if me.validator is not None: return
        tools = {}
        TAB=4*' '
        oldDoc = ('\n'+2*TAB).join( t.strip() for t in sorted( me._validators.oldDoc))
        newDoc = ('\n'+TAB  ).join( t.strip() for t in sorted( me._validators.newDoc))
        unchanged_fields_at_upd_del = sorted( t.strip() for t in me._validators.unchanged_fields_at_upd_del)

        me.validator = ('''
if (_user_is_admin()) return;
if (oldDoc) {
    ''' + oldDoc + '''
    if (oldDoc._deleted) _forbidden_non_admin();    //no updating a deleted one
    else if (!newDoc._deleted) {
        ''' + ' '.join( '_unchanged( "'+u+'");' for u in unchanged_fields_at_upd_del) + '''
    } //!oldDoc._deleted && !newDoc._deleted
} //oldDoc
''' + newDoc
        )

        for k,t in ValidatorDefinition.tools.tools().items():
            if k+'(' in me.validator:
                tools[ k] = t
        for t in me._validators.tools:
            t = t.strip()
            if not t: continue
            if t in tools: continue
            #assert t.startswith( 'function ')
            #assert '(' in t and ')' in t
            #assert '{' in t and '}' in t
            tools[ t] = t
        tools = '\n'.join( TAB+t.strip() for t in sorted( tools.values()))
        me.validator = tools + me.validator

        ValidatorDefinition.prepare( me)

class ViewDefinition( DesignDefinition):

    #XXX include_docs=True saves index.space but is extra lookup per row (+race cond)
    #there is builtin log(x) func in javascript views
    #.ini: log_level = debug -> reduce calls go to log
    #most errors go only to log

    '''
    map_fun : autowraps into proper function(..) { }
    reduce_fun: autowraps into proper function(..) { } unless the text starts with _
    map_fun = 'if ... emit( %(SEQ)s, %(DOC)s ); '
        autoreplaces SEQ with seq_field (single or list), and DOC with null or doc depending on include_docs
    e.g.
    seq_field = ('stamp', SEQ_FIELDNAME or client.TemporaryView.local_seq, )

    '''

    def __init__( me, name, **ka):
        me._args = name, ka.copy()
        include_docs = ka.get( 'include_docs', False)
        seq_field = ka.pop( 'seq_field', None)

        map_fun = ka[ 'map_fun'].strip()
        reduce_fun = (ka.get( 'reduce_fun') or '').strip()

        substs = dict(
                DOC= include_docs and 'null' or 'doc',
        )
        seq_field_init = '-1111.0'
        if seq_field:
            if isinstance( seq_field, basestring): seq_field = seq_field.split()

            seq_fieldx  = [ s if s.startswith( '(') else 'doc.'+s for s in seq_field ]
                #SEQ= 'parseInt( doc.%s)' % seq_field
            seq_field_safe = '%(SEQ)s ? %(SEQ)s : 0'
            if len(seq_field) <2:
                seq_fieldx = seq_fieldx[0]
                substs.update(
                        SEQ = seq_fieldx,
                        SEQ_INIT4MAX = seq_field_init,
                        SEQ_SAFE = seq_field_safe % dict( SEQ= seq_fieldx),
                        )
            else:
                for k,ss in dict(
                        SEQ         = seq_fieldx,
                        SEQ_INIT4MAX= (seq_field_init for s in seq_fieldx),
                        SEQ_SAFE    = (seq_field_safe % dict( SEQ= s) for s in seq_fieldx),
                        ).items():
                    substs[ k] = '['+ ','.join( ss) + ']'

        map_fun    = map_fun % substs
        reduce_fun = reduce_fun % substs or None
        me.mapred = DictAttr(
            map_fun    = map_fun ,
            reduce_fun = reduce_fun,
            seq_field  = seq_field,
            seq_field_init = seq_field_init,
            )

        if not map_fun.startswith( 'function('):
            map_fun = '\n'.join( [ 'function(doc) {', map_fun, '}' ])
        if reduce_fun and not reduce_fun.startswith( 'function(') and not reduce_fun.startswith('_'):
            reduce_fun = '\n'.join( [ 'function( keys, values, rereduce) {', reduce_fun, '}' ])

        ka.update( map_fun= map_fun, reduce_fun= reduce_fun)

        DesignDefinition.__init__( me, name, **ka)

    def clone( me, **ka):
        name, kargs = me._args
        return me.__class__( name= name, **dict( kargs, **ka))

    def query( me, db, tmp= False, **ka):
        #print( 33333333333, me.name, tmp, ka)
        if tmp: #exec as immediate temp view
            return db.query(
                map_fun     = me.map_fun,
                reduce_fun  = me.reduce_fun,
                language    = me.language,
                wrapper     = me.wrapper,
                **dict( me.defaults, **ka))
        return me.__call__( db, **ka)



#TODO   http://wiki.apache.org/couchdb/Document_Update_Validation
#       http://wiki.apache.org/couchdb/Document_Update_Handlers

'''
{
  .."_id": "_design/myview", ..

    #one per design-doc - to have multiple, needs multiple design docs; EACH doc goes through ALL validators
  "validate_doc_update": "function(newDoc, oldDoc, userCtx, secObj) {
        if (newDoc.address === undefined) {
                 throw({forbidden: 'Document must have an address.'});
        }"


    #these can be multiple, like 'views'. can autocreate
  "updates": {
    "hello" : "function(doc, req) {
      if (!doc) {
        if (req.id) {
          return [{
            _id : req.id
          }, 'New World']
        }
        return [null, 'Empty World'];
      }
      doc.world = 'hello';
      doc.edited_by = req.userCtx;
      return [doc, 'hello doc'];
    }",

    "in-place" : "function(doc, req) {
      var field = req.form.field;
      var value = req.form.value;
      var message = 'set '+field+' to '+value;
      doc[field] = value;
      return [doc, message];
    }",

  "filters": {
      "myfilter": "function goes here"
    }
  ...

'''

if __name__ == '__main__':
    q_people_all = ViewDefinition( name= 'people/all', db= 'discus',
        map_fun= ''' function( doc) {
            if (doc.type == 'person') emit( %(SEQ)s, %(DOC)s );
            } ''',  # no need for [doc.name,doc.seq]
            include_docs =False,
        )

# vim:ts=4:sw=4:expandtab
