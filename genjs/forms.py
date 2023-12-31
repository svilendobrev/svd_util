from common_helpers.genjs.genjsui import *
from collections import OrderedDict as dictOrder

js_select4nomencl = '''
var _select4nomencl_cache = {}
var select4nomencl = function( nomtype) {
    var c = _select4nomencl_cache[ nomtype ]
    if (c) return c
    c = _select4nomencl_cache[ nomtype ] = Object.entries( all.nomencl[ nomtype ]).sort()
    return c
}
'''

js_instantiator = '''
var instantiator = function( schema, do_filter) {   //, timer
    var getClass = {}.toString
    var isfunction = function( object) {
        return object && getClass.call(object) === '[object Function]';
        }
    for (var rsrc in schema) {
        var rschema = schema[ rsrc]
        rschema = do_filter ? rschema.filter : rschema.schema
        for (var field in rschema) {
            var fschema = rschema[ field]
            for (var k in fschema) {
                var v = fschema[k]
                if (isfunction( v ))
                    fschema[ k ] = v()
                    //if (tmr) timer( [field,k], 0)
            }
        }
    }
}
'''

class Gen_form:
    EDITOR = True
    predefineds = [ js_select4nomencl, js_instantiator ]
    link_type = 'string'
    def attributes( me): return super().attributes() + 'select4nomencl instantiator'.split()
    #nomenclsWithCode = ()
    #def field2choices( me, field): ...
    #element = element
    #func_getValue = func_getValue
    def templates( me):
        element = me.element
        class func( me.func_getValue):
            func = 'function()'
        func_return = func._return

                # validator=[]
        def date( field): return dict( type= 'string',)
        def datetime( field): return dict( type= 'string',)

        #@func_attrs( ui=dict( widget= 'updown'))
                #minimum= 0,
        def number( field): return dict( type= 'integer',)
        def number_float( field): return dict( type= 'float',)
        def text( field): return dict( type= 'string',)
        def textshort( field): return dict( type= 'string',)
        def textlong( field):  return dict( type= 'string',)

        def textdigits( field): return dict(
                type= 'string',
                pattern= rstr('^\\d+$'),
                )

        def onoff( field): return dict( type= 'boolean',)

        def nomencl( field, nomtype):
            #inclCode = nomtype in me.nomenclsWithCode
            def sn( *a): #inclCode, keyOnly):
                return func_return( 'all.select4nomencl( ' + quote(nomtype) #+ ', ' + jstr4bool(inclCode)
                    #+ ', ' + jstr4bool(keyOnly)
                    + ' )')
            return dict(
                type        = 'string',
                enum        = sn(),
                #enum        = sn( inclCode, True),
                #withcode    = inclCode,
                #enumKeys    = sn( False, True),
                #enumValues  = sn( False, False),
                #enumKeyValues= sn( True, False),
                totype      = nomtype,
                )

                # validator= []  # jstr('double') TODO: use better/custom/ validator
        def money( field): return dict( type= 'integer',)

        def link( field, relmodel =None, config =None): return dict(
                totype= relmodel,
                meaning= 'link-id-of-something-else',
                type= me.link_type,
                )

        def choice( field): return dict(
                type= 'enum_string',
                values = me.field2choices( field),
                )
        def multichoice( field): return dict( choice( field), many= True, template='choice')

        def file( field): return dict( type= 'file',)
        def object( field, relmodel =None): return dict(
                totype= relmodel,
                meaning= 'sub-object',
                type= 'object'
                )

        return locals()

    def conf( me, fields, resource_name, **ka):
        assert me.EDITOR
        return dict(
                schema = me.schema_for_fields( fields, pfx4css= resource_name+'-'),
                **ka
                )
    def make_schema( me, *a,**ka):
        r = super().make_schema( *a,**ka)
        #r.update( title= name.capitalize())
        ui = getattr( r._ctx.templator[0], 'ui', None)
        if ui: r.update( ui= ui)
        return r

# vim:ts=4:sw=4:expandtab
