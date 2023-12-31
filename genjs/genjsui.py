# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals
''' switchables
* js_gen:
** func_getValue: function vs =>
** element: createElement vs h
* head: with react or without/ =vue?
* templates: table vs editor
* setup/_cfg/config4vs: rest/serializers+viewsets vs ql/schema
* conf: table/schema_for_fields+cols vs editor/schema_for_fields+uischema_for_fields
'''
from textwrap import indent, dedent
from collections import OrderedDict as dictOrder
import sys,re
import inspect
from common_helpers.dicts import dictAttr
# from pprint import pprint, PrettyPrinter
# PrettyPrinter._dispatch[dictOrder.__repr__] = PrettyPrinter._dispatch[dict.__repr__]

TAB=2*' '
QUOTE = "'"

class jstr(str): pass
class rstr(str): pass
class qstr(str): pass

def jstr4bool(x): return jstr( str(x).lower() )

def quote(x):
    'never use repr(text) just to add "", use this'
    if isinstance( x,jstr): return x
    if isinstance( x,rstr): return repr(x)
    if not isinstance( x,str): return str(x)    #qstr is a str
    #if "'" not in x:
    #    q= "'"
    #else:
    if 1:
        q= QUOTE
        x = x.replace( QUOTE, '\\'+QUOTE)
    x = x.replace( '\n', '\\n')
    return q+x+q

class func_getValue:
    '''may use as plain func: func_getValue()
        value may come from outside i.e. getattrib( path) (but null if undefined),
        else get it from row, i.e. is row.<field_name>
    '''
    _func = 'function( value,row,name,h)'
    _arrow= '(value,row,h,value) =>'
    #config:
    func = _func

    def no_return( klas, body):
        if '\n' in body:
            body = indent( body, TAB)
            sep  = '\n'
        else:
            sep  = ' '
        return jstr( sep.join( [ klas.func + ' {', body, '}'] ))
    __new__ = no_return
    no_return = classmethod( no_return)
    @classmethod
    def with_return( klas, body):
        return klas.no_return( 'return ' + body)
    _return = with_return

class element:
    'use as plain func: element(..)'
    _el = 'createElement'
    _h = 'h'
    #config:
    creator = _el
    items_always = False
    attrs_extra = False
    def element( _klas_, tag, *items, **attrs):
        'inside context having row (and h=builder)'
        _cfg = _klas_
        if attrs:
            attrs = ',\n'.join(
                k+': '+( v if isinstance( v,str) and 'row.' in v else quote( v))
                for k,v in sorted( attrs.items()))
        else: attrs = ''
        items = [ quote(i) for i in items ]
        if items:
            items = '\n' + ',\n'.join( indent( i, TAB) for i in items)
        else:
            items = ''
        if attrs:
            attrs = '\n'+indent( attrs, 2*TAB ) + '\n'+TAB
            if _cfg.attrs_extra: attrs = ' attrs: {' + attrs + '}'
        if items or _cfg.items_always:
            items = '[' + items + bool(items)*'\n' + ']'

        return jstr(
            _cfg.creator + '( "'+tag+'", {'
            + attrs
            + '}, '
            #+ bool(items)*', '
            + items
            + ')')
    __new__ = element
    element = classmethod( element)

NO_COMMENTS = False
KEYS_QUOTED = False
#’
#–
#—
#ÿ
# 0x0b ctrl-k

def str_dict_rows( d, as_list =None):
    'takes dict(k,v) or list(v), v can be dict, list, int, str, or else repr(); differs str, jstr, rstr'
    islist = isinstance( d, (list,tuple))
    if as_list is None: as_list = islist
    r = [ as_list and '[' or '{']
    cmnt= None
    for k,v in enumerate(d) if islist else sorted( d.items()):
        if isinstance( v, (dict,list,tuple)): sv = str_dict_rows( v)
        elif isinstance( v, bool): sv = str(v).lower()
        elif isinstance( v, (str,int)): sv = quote(v)
        elif v is None: sv = 'null'
        else: sv = repr(v)
        sv = sv.replace( '\n', '\n'+TAB)
        cmnt= ' //'+str(k) if '\n' in sv and not NO_COMMENTS else ''
        if not islist:
            if isinstance( k, qstr) or isinstance( k, str) and KEYS_QUOTED:
                k = quote( k)
            elif not isinstance(k,str) or '.' in k or '-' in k or isinstance( k,rstr):
                k = repr( k)
            r.append( TAB+k+': '+sv+','+cmnt)
        else:
            r.append( TAB+sv+','+cmnt)
    if cmnt is not None:
        r[-1] = r[-1][:-len(cmnt) if cmnt else None].rstrip(',')+cmnt
    r.append( as_list and ']' or '}')
    return '\n'.join( r)

############
EUR= '\u20ac'
EUR= '&#8364;'
EUR= '&euro;'

######
import functools
def partial( func, *a,**ka):
    f = functools.partial( func, *a,**ka)
    f.__name__ = func.__name__
    return f

re_unspecify = re.compile( 'at (?P<address>0x[0-9a-f]+)', re.IGNORECASE)
def unspecify( t):
    return re_unspecify.sub( '', t)

def globals_replace( **ka):
    r = dict( (k, globals()[k]) for k in ka)
    globals().update( ka)
    return r


class Gen:
    #EDITOR = True

    def head( me): return '''
export default { data() {
'''
    tail = '''

}}
'''.rstrip()

    predefineds = []
    def predefined( me): return me.predefineds
    def attributes( me): return []

    def __init__( me):
        if callable( me.templates): me.templates = me.templates()
        def is_nomencl( *a,**ka): raise NotImplementedError
        me._cfg = dictAttr( is_nomencl = is_nomencl,
            modelkind2template  = {},   #model_field.kind: ..
            fieldklas2template  = {},   #serlz_field_klas: ..
            name2template       = {},   #name: ..
            fieldklasi4url      = [],   #serlz_field_klas
            fieldklasi4link     = {},   #serlz_field_klas: ..
            )

    element = element
    func_getValue = func_getValue
    templates = {}  #'{ template_name: template_func }' or method returning that

    def cfg_templates( me, **ka):
        assert len(ka) == 1, ka
        name, dd = ka.popitem()
        templates = me.templates
        missing = dict( (k,v) for k,v in dd.items() if (v['f'] if isinstance(v,dict) else v) not in templates)
        if missing: me.err( '???? unknown template-names in', name, ':', missing)
        #r = dict( (k,templates[v]) for k,v in dd.items() if v in templates)
        r = dict( (k,(  templates[v] if not isinstance( v,dict) else
                        dict( v, f= templates[ v['f']] )
                        ))
                    for k,v in dd.items() if k not in missing)
        me._cfg.setdefault( name, {}).update( r)

    def setup( me):
        'all django stuff - here'

        from django.core.exceptions import FieldDoesNotExist
        me._cfg.FieldDoesNotExist = FieldDoesNotExist

        me.cfg_templates( modelkind2template = dict(
            money   = 'money',
            digits  = 'textdigits',   #TODO
            #'AGB, BSN ..':   textdigits,   #TODO
            ))
        #_cfg.fieldklas2template = ..
        #_cfg.fieldklasi4url  = ..
        #_cfg.fieldklasi4link = ..
        #_cfg.name2template =

        from django.db import models
        me.cfg_templates( modelklas2template = {
            models.DateTimeField:   'datetime',
            models.DateField:       'date',
            models.NullBooleanField: 'onoff',
            models.BooleanField:    'onoff',
            models.IntegerField:    'number',
            models.FloatField:      'number_float',
            models.CharField:       'text',
            models.TextField:       'text',
            models.UUIDField:       'text',
            models.ForeignKey:      'link',
            #models.ImageField:      'imageurl',
            #models.Field:   'text',      #anything
            #enum? :    'text',
            #enum-multi: 'multichoice',
            })

        #_cfg.is_nomencl( totype, schema) = ...

    def field2model_field( me, field, schema): ...
    def field2child_if_many( me, field, schema): ...

    ctx = None
    def strctx( me): return '?'

    #def is_link( me, field):
    #    return isinstance( field, tuple( me._cfg.fieldklasi4link))
    def by_modelfield_kind( me, modelfield, schema):
        kind = getattr( modelfield, 'kind', None)
        return kind and me._cfg.modelkind2template.get( kind)
    def by_name( me, name, schema):
        return me._cfg.name2template.get( name)

    def _by_klas( me, field, klasi):
        for klas, genfunc in klasi.items():
            if isinstance( field, klas):
                return genfunc
    def by_field_klas_link( me, field, schema):
        return me._by_klas( field, me._cfg.fieldklasi4link)
    def by_field_klas( me, field, schema):
        return me._by_klas( field, me._cfg.fieldklas2template)
    def by_modelfield_klas( me, modelfield, schema):
        return me._by_klas( modelfield, me._cfg.modelklas2template)

    def field2totype_if_link( me, field, schema):
        modelfield = schema._ctx.modelfield
        if not modelfield: return
        if modelfield.related_model: return modelfield.related_model
        if modelfield.primary_key: return modelfield.model

    def get_templator( me, field, schema):
        modelfield = me.field2model_field( field, schema)
        schema._ctx.modelfield = modelfield
        child = me.field2child_if_many( field, schema)
        many = bool( child)
        field = child or field
        args = ()
        attrs = {}
        if many: attrs.update( many= True)

        idbg = None
        genfunc = me.by_field_klas_link( field, schema)
        if genfunc:
            idbg = -1,me.by_field_klas_link
            typeto = me.field2totype_if_link( field, schema)
            if typeto:
                if me._cfg.is_nomencl( typeto, schema):
                    genfunc = me.templates[ 'nomencl']
                if not isinstance( typeto, str): typeto = typeto.__name__
                args = (typeto, )
        else:
            for ii,(byfunc,byargs) in enumerate([
                [me.by_modelfield_kind, ( modelfield, schema),], #by modelkind2template
                [me.by_name, ( schema._ctx.name, schema),     ], #by name2template
                [me.by_field_klas, ( field, schema),          ], #by fieldklas2template
                [me.by_modelfield_klas, ( modelfield, schema),], #by modelklas2template
                ]):
                genfunc = byfunc( *byargs)
                if genfunc:
                    idbg = ii,byfunc
                    break
        #if 'latitude' == field['field_name']: print( 555555555, genfunc, idbg)
        if genfunc:
            if isinstance( genfunc, dict):
                attrs.update( (k,v) for k,v in genfunc.items() if k !='f')
                genfunc = genfunc['f']
            return genfunc,args,attrs

        me.err( '? unknown field:', schema._ctx.name, '@', me.strctx(), str(field).split('\n')[0], '::', schema )

    def _make_template( me, template, schema ):
        'may return anything'
        ka = dict( config= template[2]) if 'config' in inspect.getargspec( template[0]).args else {}
        return template[0]( schema._ctx.field, *template[1], **ka)

    def make_schema( me, field, schema):
        'must return dict'
        modelfield = me.field2model_field( field, schema)
        schema._ctx.modelfield = modelfield
        if getattr( modelfield, 'primary_key', False):
            schema._ctx.primary_key = True

        def unknown( field): pass
        templator = me.get_templator( field, schema) or (unknown,(),())
        schema._ctx.templator = templator
        try:
            r = me._make_template( templator, schema)
        except:
            print( '???', name, templator)
            raise
        schema.update( templator[2], template= templator[0].__name__)
        schema.update( r or ()) #allow templator to override template= etc
        if schema._ctx.get( 'primary_key'):
            schema.update( template= 'selflink')
            if me.ctx.model: schema.update( totype= me.ctx.model.__name__)
        return schema

    def schema_for_fields( me, fields, pfx4css ='', as_list =False):
        schemas = [ (name, me.make_schema( field,
                            dictAttr( name= name, _ctx= dictAttr( field= field, name= name))))
                        for name,field in fields.items() ]
        for n,s in schemas:
            s.pop( '_ctx')
        if not as_list: schemas = dictOrder( schemas)
        return schemas

    def styles_for_field( me, name, templatename, pfx4css =''):
        pfx4 = me.EDITOR and 'e4' or 't4'
        return [ pfx4 + (pfx4css + name).replace( '.','-'),
                 pfx4 + 'kind-'+templatename, ]

    def make_schemas( me):
        'yields { schema_name: schema } ; schema_name is usualy resource_name'
        return ()

    def make_nomencls( me ):
        'yield klas_name, { code: value, .. }, descr ; descr is optional'
        return ()

    def make_others( me):
        'yield dict( name: value )'
        return {}

    outf = None
    def prn( me, *a):
        print( file= me.outf or sys.stdout, *a )
    def err( me, *a):
        msg = unspecify( ' '.join( str(x) for x in a))
        me.prn( '//', msg)
        EDITOR = getattr( me, 'EDITOR', None)
        what = me.__class__.__name__ if EDITOR is None else (EDITOR and 'FORM' or 'TABLE')
        if me.outf: print( ' //', what, msg )

    def schemas( me):
        cfgs = dictOrder()
        for cfg in me.make_schemas() or ():
            cfgs.update( cfg)
        if cfgs: return me.cfgs2schames( cfgs)

    def cfgs2schames( me, cfgs):
        return dict( schema= str_dict_rows( cfgs),)

    if 0:
      def cfgs2schames( me, cfgs):
        cache4fields = {}
        cache4fields1= {}
        def s2keyvalue( fschema):
            fschema = dict( (k,v) for k,v in fschema.items() if k!= 'name' and k!= 'className')
            return tuple( sorted((k, tuple(v) if isinstance(v,list) else v)
                for k,v in fschema.items()
                )), fschema
        for sname, schema in cfgs.items():
            for aname,avalue in schema.items():
                if not isinstance( avalue, dict): continue
                for fname, fschema in avalue.items():
                    if not isinstance( fschema, dict): continue
                    key,subschema = s2keyvalue( fschema)
                    key = str( key)
                    cache4fields.setdefault( key, []).append( (sname,aname,fname))
                    cache4fields1[ key] = subschema
        NMIN = 5
        todo = dict( (k,where) for k,where in cache4fields.items() if len(where) >= NMIN)
        cache4fields2 = {}
        cache4fields3 = {}
        attrs = 'qltype size totype template type'.split()  #name
        for nmax in range( 2,6):
            undone = {}
            for k,where in sorted( todo.items(), key= lambda kv: (kv[0],-len(kv[1]),) ):
                #print( '  ', k,len(where),)
                #$continue
                v = cache4fields1[ k ]
                #print( v)
                #key = '/'.join( str(x) for x in [v['name'], v['template'], v['qltype'], v.get('size'), v.get('totype')] if x)
                key = '___'.join( str(x) for x in [v.get(i) for i in attrs[:nmax]] if x)
                #v1set = set( s2key( v)) #str(i) for i in v.items())
                v2 = cache4fields2.get( key)
                if v2:
                    undone[ k] = where
                    #k2 = str( s2key( v2))
                    #undone[ k2 ] = cache4fields[ k2 ]
                    continue
                    #v2set = set( s2key( v2)) # str(i) for i in v2.items())
                    #if not (v1set-v2set):   #v2 bigger
                    #    key += ':' + '/'.join( str(x) for x in sorted(v2set-v1set))
                    #else:
                    #    print( v2set-v1set)
                    #    print( v1set-v2set)
                    #    assert key not in cache4fields2, (cache4fields2[key],k,v)
                cache4fields2[ key] = dict( v,
                    #w_=len(where), where=[ '/'.join(w) for w in where]
                    )
                cache4fields3[ k] = key
                print( '  ', key,len(where),v)
            todo = undone
        #assert not undone, '\n'.join(sorted( undone))
        print( 'not cached', len(undone), '\n'.join(sorted( f'{k}:{len(v)}' for k,v in undone.items())))

        for sname, schema in cfgs.items():
            for aname,avalue in schema.items():
                if not isinstance( avalue, dict): continue
                for fname, fschema in avalue.items():
                    if not isinstance( fschema, dict): continue
                    key,subschema = s2keyvalue( fschema)
                    key = str( key)
                    cachekey = cache4fields3.get( key)
                    if not cachekey: continue
                    cached = cache4fields2.get( cachekey)
                    for k in cached: fschema.pop( k,0)
                    fschema[ '__copyfrom'] = 'cache.'+cachekey

        return dict(
            cache = str_dict_rows( cache4fields2),
            schema= str_dict_rows( cfgs),
            )

    def nomencls( me):
        nomencls = {}
        nomencls_descr = {}
        for nomklas_name, nomdict, *nom_descr in me.make_nomencls() or ():
            if nomdict is not None:
               nomencls[ qstr(nomklas_name) ] = dict( (qstr(k), v) for k,v in nomdict.items() )
            if nom_descr:
                nomencls_descr[ qstr(nomklas_name) ] = nom_descr[0]
        if nomencls: return dict(
            nomencl       = str_dict_rows( nomencls, as_list= False),
            nomencl2title = str_dict_rows( nomencls_descr, as_list= False),
            )

    def others( me):
        r = me.make_others()
        if r: return dict( (k,str_dict_rows( v)) for k,v in r.items())

    def generators( me):
        return 'head nomencls others predefined all_as_gen schemas '.split()

    def all_as_gen( me):
        attrs = me.attributes()    #before generation
        return dict( all= str_dict_rows( dict( (k,jstr(k)) for k in attrs )))

    def gen( me, outf =None, as_dict =False):
        me.outf = outf

        print()
        me.err( '//// gen by', me.__class__.__mro__)

        me.setup()

        r = ['']
        prn = r.append

        attrs = []
        for g in me.generators():
            if isinstance( g, str): g = getattr( me, g)
            if callable( g): x = g()
            else: x = g
            if not x: continue
            if isinstance( x, dict):
                for k,v in sorted( x.items()):
                    attrs.append( k)
                    if as_dict:
                        x = k+': ' + v + ', //'+k
                    else:
                        x = 'var '+k+' = ' + v + ' //'+k
                    prn( x+'\n')
                continue
            if not isinstance( x, str): x = '\n'.join( x)
            prn( x+'\n')
            #TODO insert args into all
        if not as_dict:
            #after generation
            try: attrs.remove('all')
            except: pass
            if attrs:
                prn( 'Object.assign( all, ' + str_dict_rows( dict( (k,jstr(k)) for k in attrs )) + ')' )
            prn( 'return all')
        prn( me.tail)
        prn( '// vim:ts=4:sw=4:expandtab')
        me.prn( '\n'.join( r ))

    def gen_json( me, outf =None):
        'json does not have comments, and need double quotes'
        saveit = globals_replace( QUOTE = '"', NO_COMMENTS = True, KEYS_QUOTED =True)

        print()
        me.err( '//// gen by', me.__class__.__mro__)    #TODO this + version etc into below dict
        me.outf = outf  #after topline

        me.setup()

        r = []
        prn = r.append
        for g in me.generators():
            if isinstance( g, str): g = getattr( me, g)
            if callable( g): x = g()
            else: x = g
            if not x: continue
            if isinstance( x, dict):
                x = ',\n'.join( quote( k)+ ': '+ v for k,v in sorted( x.items()))
            if not isinstance( x, str): x = '\n'.join( x)
            prn( x)
        #attrs += me.attributes()    #ignore
        prn( me.tail)
        #prn( '// vim:ts=4:sw=4:expandtab')     #TODO this??
        tx_subascii = dict( (a,'\\u%04x'%a) for a in range(32) if a not in [10,13])
        tx = str.maketrans( tx_subascii)
        me.prn( '\n'.join( r ).translate( tx))
        globals_replace( **saveit)


class Gen4react:
    def head( me): return '''
import { createElement as %(element_create)s } from 'react'
''' % dict( element_create= me.element.creator) + super().head()
#//import React from 'react'


if __name__ == '__main__':
    TAB = 4*' '
    class func_getValue( func_getValue):
        func = func_getValue._func
    func_getValue_return = func_getValue._return
    class element( element):
        creator = element._h
        items_always = 1
        attrs_extra = 1

    class tests:
        t0 = element( 'input' ), '''
h( "input", {}, [])
'''
        t1 = element( 'input', 123 ), '''
h( "input", {}, [
    123
])
'''
        t2 = element( 'input', 123, checkbox='row.myfn'), '''
h( "input", { attrs: {
        checkbox: row.myfn
    }}, [
    123
])
'''
        t22 = element( 'input', 123, checkbox='row.myfn', puk=3, text='atext'), '''
h( "input", { attrs: {
        checkbox: row.myfn,
        puk: 3,
        text: 'atext'
    }}, [
    123
])
'''
        t3 = element( 'input', 123, 225, 'ter', checkbox='row.myfen'), '''
h( "input", { attrs: {
        checkbox: row.myfen
    }}, [
    123,
    225,
    'ter'
])
'''
        t4 = func_getValue._return( t2[0] ), '''
function( value,row,name,h) {
    return h( "input", { attrs: {
            checkbox: row.myfn
        }}, [
        123
    ])
}
'''
        t5 = func_getValue( 'return '+ element(
                'div', t2[0], ' ', t3[0], **{'class':'myclas'}
                )), '''
function( value,row,name,h) {
    return h( "div", { attrs: {
            class: 'myclas'
        }}, [
        h( "input", { attrs: {
                checkbox: row.myfn
            }}, [
            123
        ]),
        ' ',
        h( "input", { attrs: {
                checkbox: row.myfen
            }}, [
            123,
            225,
            'ter'
        ])
    ])
}
'''

        t6 = func_getValue_return( 'row.qweet' ), '''
function( value,row,name,h) { return row.qweet }
'''

        ts1 = str_dict_rows( dict( a=1, b='bb', c=rstr("'"), d=jstr('x'), )), '''
{
    a: 1,
    b: 'bb',
    c: "'",
    d: x
}
'''

        ts2 = str_dict_rows( dict( a=1, b=['b',5], c= dict( q=1, w= dict( o=3)), d=jstr('x'), )), '''
{
    a: 1,
    b: [
        'b',
        5
    ], //b
    c: {
        q: 1,
        w: {
            o: 3
        } //w
    }, //c
    d: x
}
'''

    import difflib
    differ = 0 and difflib.context_diff or difflib.unified_diff
    for k,v in sorted( tests.__dict__.items()):
        if k[0] !='t': continue
        print( k)
        res,exp = [i.strip() for i in v]
        if res != exp:
            for l in differ( res.split('\n'), exp.split('\n'), 'res', 'exp', ):
                print( ' ', l)
        assert res == exp

# vim:ts=4:sw=4:expandtab
