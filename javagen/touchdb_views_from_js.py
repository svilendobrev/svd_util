#!/usr/bin/env python
# -*- coding: utf-8 -*-

target_source = '''
void view( TDServer server, String DATABASE_NAME, String view_full_name, String version) {
    TDDatabase db = server.getDatabaseNamed( DATABASE_NAME);
    TDView view = db.getViewNamed( view_full_name);
            //String.format("%s/%s", dDocName, byDateViewName));
    view.setMapReduceBlocks(
      new TDViewMapBlock() {
          @Override
          public void map( Map<String, Object> document, TDViewMapEmitBlock emitter) {
            Object createdAt = document.get("created_at");
            if( createdAt != null)
                emitter.emit( createdAt.toString(), document);
          }
        },
      //null   //TDViewReduceBlock
      new TDViewReduceBlock() {
        @Override
        public Object reduce( List<Object> keys, List<Object> values, boolean rereduce) {
            ...
        } }
      , version );
}
'''

#works for cases:
#regexp: up to: if (doc.a && doc.b=='yes') emit( [ doc.a, doc.b, 2], doc ); #75%
#expr.builder, up to: emitif( condition_expr, key_expr, value_expr)     #90%
#above that: hands
#reducefuncs: hands

def gen_allviews( designs4db, predefs ={} ):
    'example'
    for dbname,views in designs4db.items():
        yield '\n'.join( i.lstrip('\n')
            for i in gen_view4db( dbname, views, predefs) )
    yield item0

head = '''
import com.couchbase.touchdb.TDDatabase;
import com.couchbase.touchdb.TDServer;
import com.couchbase.touchdb.TDView;
import com.couchbase.touchdb.TDViewMapBlock;
import com.couchbase.touchdb.TDViewReduceBlock;
import com.couchbase.touchdb.TDViewMapEmitBlock;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.Collection;
import android.util.Log;
'''


#should become static
item0 = '''\
final TDViewReduceBlock null_reduce = null;
'''

class my_builtin:
    if 0*'originals':
        js_sum= ''' function( keys, values, rereduce) {
            return sum(values);
        } '''
        js_count = ''' function( keys, values, rereduce) {
          if (rereduce) return sum(values);
          else return values.length;
        } '''

    _sum   = 'TDView.totalValues( values);'
    _count = 'touchdb.reduce_count( values, rereduce);'

    used = 0
    @classmethod
    def imports( klas): return klas.used and '''\
import com.svilendobrev.storage.touchdb;
''' or ''

def gen_view4db( dbname, views, predefs ={}):
    #predefs: { (dbname, v.design, v.name): .map_fun .reduce_fun }

    #each should become static method
    yield '''\
public
Map< String, Boolean> views4%(dbname)s( TDServer server, String version, String dbname ) {
    TDView view ;
    TDDatabase db = server.getDatabaseNamed( funk.defaults( dbname, "%(dbname)s") ); //autocreate
    Map< String, Boolean> meta_value_is_doc = new HashMap();
     String viewname;
''' % locals()

    for v in views:
        view_full_name = v.design + '/' + v.name
        predef = predefs.get( (dbname, v.design, v.name) )
        t = None
        yield '''
    viewname = "%(view_full_name)s";
    Log.v( "jviews", viewname );
    view = db.getViewNamed( viewname );''' % locals()
        yield '''
    view.setMapReduceBlocks(
      new TDViewMapBlock() {
        @Override'''

        if predef and predef.map_fun:
            for y in predef.map_fun(v):
                yield y.replace('\n', '''
        ''')
        else:
            yield '''
        public void map( Map<String, Object> doc, TDViewMapEmitBlock emitter) {
        '''.rstrip()
            t = translator()
            ok = False
            for i in t.translate_map( v.mapred.map_fun ):
                yield '''
            '''+i
                ok = True
            if not ok:
                yield ''' /*
            XXX ''' + v.mapred.map_fun + '*/'
            yield '''
        } //map'''

        yield '''
      }, //TDViewMapBlock'''

        reduce_fun = v.mapred.reduce_fun
        if reduce_fun:
            yield '''
      new TDViewReduceBlock() {
        @Override'''

            if predef and predef.reduce_fun:
                for y in predef.reduce_fun(v):
                    yield y.replace('\n', '''
        ''')
            else:
                result = getattr( my_builtin, reduce_fun, None)
                if result: my_builtin.used+=1
                if not result:
                    result = '''null;
                /* XXX ''' + reduce_fun + ' */'
                yield '''
        public Object reduce( List<Object> keys, List<Object> values, boolean rereduce) {
            return %(result)s
        } //reduce''' % locals()

            yield '''
      } //TDViewReduceBlock'''
        else:
            yield '''
      null_reduce'''
        value_is_doc = t and t.values == [ 'doc' ] and 'true' or 'false'
        yield '''
      , version
    );
    meta_value_is_doc.put( viewname, %(value_is_doc)s );
''' % locals()

    yield '''
    return meta_value_is_doc;
} // views4%(dbname)s
''' % locals()

def gen_view4all( dbnames):
    return '''\
public
void views( TDServer server, String version,
    Map< String, String> dbname2dbname,
    Map< String, Map< String, Boolean>> out_dbname2view2value_is_doc
) {
    Map< String, Boolean> meta_value_is_doc;
    String dbname;
''' + ''.join( '''\
    dbname = funk.get( dbname2dbname, "%(dbname)s", "%(dbname)s" );
    meta_value_is_doc = views4%(dbname)s( server, version, dbname );
    if (out_dbname2view2value_is_doc != null) out_dbname2view2value_is_doc.put( dbname, meta_value_is_doc );
''' % locals()
    for dbname in dbnames
) + '}'


if 0:
    map_fun = ''' if (doc.type == 'person') emit( %(SEQ)s, %(DOC)s ); '''
    map_fun = ''' if (doc.type == 'person')
                  if (typeof( doc.person) === 'string') emit( doc.person, doc );
                  else for (var name in doc.person) emit( name, doc );
    '''

    def js2java( map_fun):
        '''
    if (doc.x) ->
        Object doc_x = doc.get( "x");
        if (doc_x != null)

    if (doc.x == "y") ->
        Object doc_x = doc.get( "x");
        if (doc_x != null && "y".equals( doc_x.toString()))

    emit( doc.a, doc.b ) ->
           (if not already doc_x)
        Object doc_a = doc.get( "a");

    '''
        pass


tab = 4*' '
from svd_util.dicts import DictAttr

import re
doc_attr  = 'doc \. (?P<attr>\w+)'
doc_attr1 = doc_attr.replace( 'attr', 'attr1')
doc_attr2 = doc_attr.replace( 'attr', 'attr2')
doc_attr3 = doc_attr.replace( 'attr', 'attr3')
op        = '(?P<op>[=!]=)'
op1       = op.replace( 'op', 'op1')
op2       = op.replace( 'op', 'op2')
lop       = '(?P<bool>&&|\|\|)'
string    = '''['"](?P<str>[^'"]*)['"]'''
#emit_key  = 'emit\( (?P<key>\[ [^]]+\]|[^,[]+) ,' #from cconly.emit_fix
emit_key  = ('emit\( (?P<key>'+'''
    [^,[]+ |
    o [^c]+ c |
    o [^c]* o [^c]* c [^c]* c
    '''.replace( ' ','').replace( '\n','').replace( 'o',r'\[').replace( 'c',r'\]')
    +') ,'
    )

emit_value= '(?P<value>\S+) \)'
exist_attr = '(?P<not>!)?'+doc_attr
equal_str  = doc_attr1 + ' ' + op1 + ' ' + string
equal_attr = doc_attr2 + ' ' + op2 + ' ' + doc_attr3


cond = '({exist_attr}|{equal_str}|{equal_attr})'.format( **locals())
cond2= cond.replace( '<', '<y')
re_if_emit = re.compile(
 'if \( (?P<cond>({cond})( {lop} ({cond2}))*) \)'
 '\s*{emit_key} {emit_value}'
 .format( **locals())
 .replace( ' ', ' *')
)

re_cond = re.compile( ('^'+cond+'$')
 .replace( ' ', ' *')
)

key1 = '({doc_attr}|{string})'
re_key1 = re.compile( key1
 .format( **locals())
 .replace( ' ', ' *')
)

def dd(x): return 'doc_'+x
def ss(x): return '"'+x+'"'

class translator:
    def __init__( me):
        me.attrs = {}

    def exist_attr( me, attr, neg =False):
        eq = neg and '=' or '!'
        r = attr + ' ' + eq +'= null'
        r+= '   // ' + (neg and '!' or '') + 'exist_attr( '+attr+' )'
        return r
    def eq_attr2str( me, attr, str, neg =False):
        r = ''
        if neg: r += '!( '
        r += attr+ ' != null && ' + ss(str)+ '.equals( '+ attr+ '.toString() )'     #or (String)attr ??
        if neg: r+= ' )'
        r+= '   // eq_attr2str( ' + attr+ ', '+ ss(str) + ')'
        return r
    def eq_attr2attr( me, attr2, attr3, neg =False):
        r = ''
        if neg: r += '!( '
        r+= attr2+ ' == null && '+ attr3+ ' == null || '
        r+= attr2+ ' != null && '+ attr3+ ' != null && '+ attr2+ ' == '+ attr3    #XXX? weak
        if neg: r+= ' )'
        r+= '   // eq_attr2attr( ' + attr2+ ', '+ attr3+ ')'
        return r

    def if_cond( me, cond):
        attrs = me.attrs
        orcond = cond.split( '||' )
        lorcond = len( orcond)>1
        if lorcond: yield '( //||'
        for l,orc in enumerate( orcond):
            if l: yield ') || ('

            for n,c in enumerate( orc.split( '&&')):
                if n: yield ' &&'

                mc = re_cond.match( c.strip() )
                assert mc
                d = DictAttr( mc.groupdict())

                for a in '',1,2,3:
                    a = 'attr'+str(a)
                    attr = d.get( a)
                    if attr:
                        dattr = d[a] = dd( attr)
                        attrs[ attr] = dattr #'Object %(dattr)s = doc.get( "%(attr)s");' % locals()

                if d.attr:
                    yield me.exist_attr( d.attr, d['not'])
                elif d.attr1:
                    yield me.eq_attr2str( d.attr1, d.str, d.op1 == '!=')
                elif d.attr2:
                    yield me.eq_attr2attr( d.attr2, d.attr3, d.op2 == '!=')
        if lorcond: yield ') //||'

    def subattr( me, m):
        attr = m.group( 'attr')
        assert attr
        dattr = dd( attr)
        attrs = me.attrs
        if attr not in attrs:
            attrs[ attr] = dattr #taa'xObject %(dattr)s = doc.get( "%(attr)s");' % locals()
        return dattr

    def emit_key( me, key ):
        rek = key
        orcond = rek.split( '||' )
        if len( orcond)>1:
            rek = 'funk.first_non_null( ' + ', '.join( orcond) + ' )'
        rek = re.sub( doc_attr
            .replace( ' ', ' *')
            , me.subattr, rek)

        rek = re.sub( ' *\]', ' }', rek)
        rek = re.sub( '\[ *', 'new Object[] { ', rek)
        yield rek

    def emit_value( me, value):
        return me.emit_key( value)

    def decl( me, attr, dattr):
        #dattr = dd( attr)
        return 'Object %(dattr)s = doc.get( "%(attr)s");' % locals()

    def translate_map( me, map_fun):
        map_fun = map_fun.strip()
        m = re_if_emit.search( map_fun)
        if not m: return

        g = DictAttr( m.groupdict())

        me.attrs = {}
        ifs = list( me.if_cond( g.cond.strip() ))
        for a,da in sorted( me.attrs.items()):
            yield me.decl( a,da)

        yield 'if ('
        for i in ifs: yield tab+i
        yield ')'
        attrs = me.attrs.copy()
        me.keys   = list( me.emit_key( g.key.strip()) )
        me.values = list( me.emit_value( g.value.strip()) )
        if len( me.attrs) > len( attrs ):
            yield '{'
            for a,da in sorted( me.attrs.items()):
                if a not in attrs:
                    yield '  '+me.decl( a,da)

        yield '  emitter.emit('
        for i in me.keys:   yield tab+i
        yield '  ,'
        for i in me.values: yield tab+i
        yield '  );'

        if len( me.attrs) > len( attrs ):
            yield '}'

        #return attrs, ifs, emit_keys, emit_values


if __name__ == '__main__':
    #import hcconly, place
    import inspect
    from svd_util import dbg
    def getdefaultarg( func, k):
        return dbg.getdefaultargs_wrap( func)[k]

    t = translator()

    def testit( tests, func, attrs0):
        print '----'*5
        print func.__name__
        ok = er = 0
        for i in tests.split('\n'):
            i = i.strip()
            if not i: continue
            print '::', i
            t.attrs = attrs0.copy()
            r = list( func( i) )
            print '\n'.join( sorted( t.attrs.values()) )
            if not r:
                print '???????'
                er+=1
            else:
                ok+=1
                print '\n'.join( r )
            print
        print 'ok', ok, 'err', er

    testit( '''
        doc.discu && doc.type != 'db'
        doc.discu && doc.type && doc.type != 'db'
        doc.type == 'title'
        doc.type!= 'title'
        doc.aide
        !doc.aide && doc.neide
        doc.aide == doc.neide
        ''', t.if_cond, {})

    testit( '''
        doc.discu
        doc.another
        "some"
        [ doc.discu, "some",doc.seq]
        [ doc.discu, doc.stamp,doc.seq]
        [ doc.discu, [doc.stamp,doc.seq]]
        ''', t.emit_key, dict( discu= 'predef doc_discu') )

    testit( '''
        null
        doc
        doc.discu
        doc.another
        ["some", doc.it]
        ''', t.emit_value, dict( discu= 'predef doc_discu') )

#if 0:
    import cu
    import itertools
    ok = er = 0
    for kind, map_funs in [ ('test', [
        ''' if (doc.discu && doc.type != 'db') emit( doc.discu, null ); ''',
        ''' if (doc.discu && doc.type && doc.type != 'db') emit( k,v ); ''',
        ''' if (doc.type == 'title') emit( k,v); ''',
        ''' if (doc.type!= 'title') emit(k,v); ''',
        ''' if (doc.aide)  emit( k,v); ''',
        ''' if (!doc.aide && doc.neide) emit( k,v); ''',
        ''' if (doc.aide == doc.neide) emit( k,v); ''',
        #cu.Discussioner2c._q_title_all,
        #getdefaultarg( cu.Channel4user.q_dbs, 'view'),
        #hcconly.Map_Discu2User._q_discu_users,
        #getdefaultarg( place.Places.q_places_by_owner, 'view'),
        ]) ] + cu.DesignDefinition.designs4db.items() :
        for map_fun in map_funs:
            print
            print kind, map_fun
            if not isinstance( map_fun, str):
                map_fun = map_fun.mapred.map_fun
                print map_fun
            t = translator()

            r = list( t.translate_map( map_fun))
            if not r:
                print '???????'
                er+=1
            else:
                #attrs, ifs, emit_keys, emit_values
                ok +=1

                #print '\n'.join( r[-1].values() )
                #print '\n  '.join( r)

    print 'ok', ok, 'err', er

# vim:ts=4:sw=4:expandtab
