from common_helpers.genjs.genjsui import *

js_moneyfmt = '''
var moneyfmt = function( m) {
    return '' + Math.floor(m/100) +'.'+ ('0'+m%100).slice(-2)
}
'''
js_moneyfmt_EUR = js_moneyfmt.replace( '\n}', ' + '+EUR+'\n}')

js_nomencl_get = '''
var nomencl_get = function( value, row, fieldname, h, nomtype, both) {
    if (value !== undefined && value !== null) {
        if (nomtype === undefined) return value; //code only
        if (both === undefined) return all.nomencl[ nomtype ][ value ] ; //text only
        return value + ": " + all.nomencl[ nomtype ][ value ] ;  //both
        }
    }
'''

retvalue0 = 'if (value !== undefined && value !== null) return '

class Gen_table:
    EDITOR = False

    #these for filters
    Gen_form = None
    _gform = None
    def make_gform( me):
        f = me._gform
        if not f:
            f = me._gform = me.Gen_form()       #TODO select4nomencl/instantiator seems not needed?
            f.outf = me.outf
            f.setup()
            f.by_modelfield_klas = lambda *a,**ka: None     #XXX no guessing by modelfield, maybe also by_name, by_modelfield_kind ...???
            f.is_FILTER = True
        return f

    predefineds = [ js_moneyfmt, js_nomencl_get ]
    def predefined( me):
        return super().predefined() + [ '''
var onoff = ''' + me.func_getValue( retvalue0 +
                    me.element( 'input', type= 'checkbox',
                        checked= jstr('value'), readOnly= jstr4bool( True),
                        tabIndex= -1,   #not tabbable
                        ))
        ] + (me._gform.predefined() if me._gform else [])
    def attributes( me):
        return super().attributes() + 'moneyfmt nomencl_get onoff'.split() + (me._gform.attributes() if me._gform else [])

    #element = element
    #func_getValue = func_getValue
    def templates( me):
        element = me.element
        func_getValue = me.func_getValue
        func_getValue_return = func_getValue._return

        def date( field): pass
        def datetime( field): pass
        def number( field): pass
        def number_float( field): pass
        def text( field): pass
        def textdigits( field): pass

        def link( field, relmodel =None, config=None): return dict( totype= relmodel)

        def choice( field): pass
        def multichoice( field): return dict( many= True, template='choice')

        def onoff( field ):
            return dict( getValue= func_getValue_return( 'all.onoff( value,row,name,h)'))

        def nomencl( field, nomtype):
            return dict( getValue= func_getValue( 'return all.nomencl_get( value,row,name,h, ' + quote(nomtype) + ', true )'))   #+ quote( field.field_name)

        def money( field):
            return dict( getValue= func_getValue( retvalue0 + 'all.moneyfmt( value )' ))

        def button( field): pass     #TODO  no, leave it to glue layer
        #def link2url( field): pass
        def file( field): pass
        def object( field, relmodel =None): return dict( totype= relmodel,)

        return locals()

    if 0:
        css4kind = {
            number: 's4kind-number',
            money:  's4kind-money',
            #..
        }

    def templates_nomencl_separate_code_text( me, fields, templators =None):
        if templators is None: templators = me.all_templators( fields)
        tnom = dictAttr( (k,me.templates[k]) for k in 'nomencl nomencl_code nomencl_text'.split())
        r = []
        for name,template in templators.items():
            if template[0] is tnom.nomencl: r += [
                    (name+'-code', me.make_schema( (tnom.nomencl_code,)+template[1:], name, fields)),
                    (name+'-text', me.make_schema( (tnom.nomencl_text,)+template[1:], name, fields)),
                    ]
        return [ (name, tmpl) for name,tmpl in r if tmpl ]

    def _make_template( me, *a,**ka):
        r = super()._make_template( *a,**ka)
        #if r and not isinstance( r, dict): return dict( getValue= r)
        return r or {}

    def conf( me, fields, resource_name, **ka):
        assert not me.EDITOR

        pfx4css = resource_name+'-'
        templates = me.schema_for_fields( fields, pfx4css= pfx4css)
        return dict(
            schema = dict(
                (name,dict(
                    #title   = name.capitalize(),
                    className= ' '.join( me.styles_for_field( name, template['template'], pfx4css )),
                    **template)
                )
                for name, template in sorted( templates.items())
            ),
            **ka)

# vim:ts=4:sw=4:expandtab
