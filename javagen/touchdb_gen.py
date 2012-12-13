#!/usr/bin/env python
# -*- coding: utf-8 -*-

import touchdb_views_from_js as jviews
#jviews-js2java works for cases:
# regexp: up to: if (doc.a && doc.b=='yes') emit( [ doc.a, doc.b, 2], doc ); #75%
# expr.builder, up to: emitif( condition_expr, key_expr, value_expr)     #90%
# above that: hands
# reducefuncs: hands

from svd_util.javagen import jgenerator as jg
from svd_util.struct import DictAttr

class Types:
    id      = jg.Text
    text    = jg.Text
    int     = jg.Int
    float   = jg.Float
    bool    = jg.Bool

    class type( jg.Text):
        no_save = True
        #no_dump = True
        def __init__( me, type):
            jg.Text.__init__( me, no_save_but_value= type)

if 1: #class Models0:
    class Model( jg.Model):
        _id  = Types.id( as_getKey =True)
        _rev = jg.Text()
        NO_MAPPING = True

#TODO: type, _id, _rev,

class java( jg.java):
    types = dict( jg.java.types,)
    types.update( {
        Types.type  : 'String',
        jg.Float    : 'Double',
        jg.Int      : 'Integer',
        jg.Bool     : 'Boolean',
        jg.TimeStamp: 'Date',
        #jg.Long  : 'Long',
    } )
    defaults = dict( jg.java.defaults,
                    String= 'null', #_notSetYet
                    Int   = 'null',
                    Double= 'null',
                    Date  = 'null',
                    Boolean= 'null',
                )

    type_of_id = 'long'
    D = DictAttr
    dbtypes = {
        'String': D( load= 'touchdb.db2string( %(arg)s)', value= '"%(value)s"' ),
        jg.Int  : D( load= 'touchdb.db2int(    %(arg)s)' ),
        #jg.Long: D( load= 'touchdb.db2long(   %(arg)s)' ),
        jg.Float: D( load= 'touchdb.db2float(  %(arg)s)' ),
        jg.Bool : D( load= 'touchdb.db2bool(   %(arg)s)' ), #set ='touchdb.bool2db' ),
        jg.TimeStamp: D( load= 'touchdb.db2TimeStamp( touchdb.db2float( %(arg)s, c))', set= 'touchdb.TimeStamp2db' ),
        #BLOB    :D( load= 'touchdb.sql2blob( %(arg)s, c)', ),
    }

    annotations = dict(
        _id = '@JsonProperty("_id")',
        _rev= '@JsonProperty("_rev")',
    )

    def touchdb( me, klas):
        dialect = klas._dialects.sqlite
        if dialect.notapplicable: return
        item_name = klas.__name__
        model_name = me.models_klas + '.' + item_name

        dbtypes_get = dict( (k,d.load) for k,d in me.dbtypes.iteritems() if d)
        load = ''
        save = ''

        namesize = me.namesize( klas)
        no_save_but_value = {}
        for name,typ,extname in dialect.iter_name_type_extname():
            dbdef = me.get_by_type( typ, me.dbtypes)
            if dbdef is None: continue

            item_attr = 'item.'+name

            arg = arg_set = item_attr

            setter = dbdef.get('set')
            if setter: arg_set = setter+'( '+item_attr+ ')'
            arg = arg.ljust( namesize + len(item_attr) - len(name) )
            arg_set = arg_set.ljust( namesize + len(arg_set) - len(name) )

            name4save = '"%(extname)s"' % locals()
            name4savej = extname == name and name4save.ljust( 2+namesize) or name4save

            if not typ.no_save:
                save += '''\
        if (%(arg)s != null) c.put( %(name4savej)s, %(arg_set)s ); else c.remove( %(name4save)s );
''' % locals()
            elif typ.no_save_but_value is not None:
                value = typ.no_save_but_value
                valuer = dbdef.get( 'value')
                if valuer: value = valuer % locals()
                no_save_but_value[ name ] = me.types[ typ.__class__], value
                save += '''\
        c.put( %(name4save)s, consts.%(name)s );
''' % locals()

            arg = 'c.get( "%(extname)s" )' % locals()
            load += me.assign_item( name, typ, arg= arg, convertors= dbtypes_get, ljustify= namesize, indent='''\
        ''') % locals()

        if not no_save_but_value: no_save_but_value = ''
        else: no_save_but_value = '''
    static public class consts {'''+''.join( '''
        static public %(type)s %(name)s = %(value)s;''' % locals()
                    for name, (type,value) in no_save_but_value.items()
                )+'''
    };
'''
        load = load.rstrip()
        return '''\
public
class %(item_name)s extends touchdb.Base {
    static public %(item_name)s base;
    public %(item_name)s() { super(); base = this; }
    static
    public %(model_name)s _factory() { return new %(model_name)s(); }
    @Override
    public Class modelClass() { return %(model_name)s.class; }
    @Override
    public ObjectNode save( Model x, JsonNode r) {
        ObjectNode c = (r==null) ? touchdb.jsonObject() : (ObjectNode)r;
        %(model_name)s item = (%(model_name)s)x;
%(save)s
        return c;
    }
    @Override
    public Model load( Model x, JsonNode c) {
        return load_org( x==null ? _factory() : (%(model_name)s)x, c);
    }
    //@Override
    public Model factory() { return _factory(); }
    static
    public %(model_name)s load_org( %(model_name)s item, JsonNode c) {
        if (item == null) item = _factory();
%(load)s
        return item;
    }
    static public %(model_name)s load_org( JsonNode c) { return load_org( null, c); }
/*
    static public List< %(model_name)s>
    load_org( ViewResult vr, List< %(model_name)s> r, Boolean use_value) {
        if (r==null) r = new ArrayList();
        for (ViewResult.Row x: vr.getRows())
            r.add( load_org( touchdb.row2doc( x, use_value)));
        return r;
    }
    static public List< %(model_name)s> load_org_doc(   ViewResult vr, List< %(model_name)s> r) { return load_org( vr, r, false); }
    static public List< %(model_name)s> load_org_value( ViewResult vr, List< %(model_name)s> r) { return load_org( vr, r, true); }
    static public List< %(model_name)s> load_org_guess( ViewResult vr, List< %(model_name)s> r) { return load_org( vr, r, null); }
    static public List< %(model_name)s> load_org( ViewResult vr, List< %(model_name)s> r)       { return load_org_guess( vr, r); }
    static public List< %(model_name)s> load_org( ViewResult vr, boolean use_value) { return load_org( vr, null, use_value); }
    static public List< %(model_name)s> load_org_doc( ViewResult vr)   { return load_org_doc( vr, null); }
    static public List< %(model_name)s> load_org_value( ViewResult vr) { return load_org_value( vr, null); }
    static public List< %(model_name)s> load_org_guess( ViewResult vr) { return load_org_guess( vr, null); }
    static public List< %(model_name)s> load_org( ViewResult vr)       { return load_org_guess( vr); }
*/
%(no_save_but_value)s
} //%(item_name)s
''' % locals()

    sqlite = touchdb

    def save_dbviews( me, designs4db, predefs ={}, mainklas ='genViews4Touchdb', exclude =(), **ka):
        dv = dict( (dbname,views) for dbname,views in designs4db.items() if dbname not in exclude )
        generated_views = [ jviews.item0 ] + [
                '\n'.join( i.lstrip('\n')
                        for i in jviews.gen_view4db( dbname, views, predefs) )
                for dbname,views in dv.items()
                ]
        ka.setdefault( 'head0', jviews.head + jviews.reduces_builtin.imports() )
        me.save_klasi( mainklas,
            klasi= generated_views + [ jviews.gen_view4all( dv) ],
            **ka
            )

    def save_models( me, mainklas ='genModels', klasi =[], **ka):
        ka.setdefault( 'head0', '''
import com.fasterxml.jackson.annotation.JsonProperty;
''')
#        klasi = klasi + [ '''
#public final String _notSetYet = '<notSetYet>';
#''']
        return jg.java.save_models( me, mainklas= mainklas, klasi= klasi, **ka)

    sqlite = touchdb

    def save_dbio( me, mainklas ='genTouchdb', klasi =[], **ka):
        ka.setdefault( 'head0', '''
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
//import com.fasterxml.jackson.databind.node.JsonNodeFactory;
//import org.ektorp.ViewQuery;
//import org.ektorp.ViewResult;
//import java.util.ArrayList;
//import java.util.List;
''')
        return me.save_sqlites( mainklas, klasi=klasi, **ka)

# vim:ts=4:sw=4:expandtab
