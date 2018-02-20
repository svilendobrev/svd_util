#!/usr/bin/env python
# -*- coding: utf-8 -*-
#s.dobrev 2k3
from __future__ import print_function #,unicode_literals

#from fielddata import FieldUndefinedError
from svd_util.attr import set_attrib, get_attrib, notSetYet

class UIController( object):
    name = ''

    def __init__( me, name =None, model =None, layout =''):
        me.model = model
        me.name = name or me.name or me.__class__.__name__
        me.layout = layout
        me.focus = None

    def action( me, context, what, **k):
        print('action:', me.name, what)
        #print me, k

    if 0:
        actors = {}
        def action( me, context, what, **k):
            #me.focus = what              #???
            try:
                actor = me.actors[ what]
            except KeyError:
                print('! no actor for', what)
            else:
                return actor( context, what )
            return None

    def redraw( me):
        return me.layout

    ERR_not_in_model = ' ! not in model: %s'

    _DBG_set_value = 1
    def set_value( me, context, fieldname, value, do_get_check =True, next_adr =None, **kargs):
        #if fieldname not in me.field_map: return
        if me._DBG_set_value: print('\n set %s ?= %r' % (fieldname, value))
        model = me.model
        oldvalue = notSetYet
        if do_get_check:
            try:
                oldvalue = get_attrib( model, fieldname)
            except AttributeError:
                e = me.ERR_not_in_model % fieldname
                print(e, model)
                return
#        if next_adr: print 'focusto', next_adr
        me.focus = next_adr or fieldname        #before set - if exception, focus goes to error field
        set_attrib( model, fieldname, value)
        if me._DBG_set_value: print(' ..=', oldvalue, ' --> %s == %r' % (fieldname, get_attrib( model, fieldname)))

    _DEFAULT_get_value = None
    _DBG_get_value = False

    def get_value( me, fieldname, err =None, do_err =True):
        model = me.model
        if me._DBG_get_value: print(' get %s in %s' % (fieldname, model))
        try:
            value = get_attrib( model, fieldname)
        except AttributeError:
            e = me.ERR_not_in_model % fieldname
            if do_err:
                print(e)
            if err is not None:
                err.append( e)
            value = me._DEFAULT_get_value
        else:
            if value is notSetYet: value = me._DEFAULT_get_value
        if me._DBG_get_value: print('   >>', value)
        return value

    field_map = {}
    ERR_not_in_fieldmap = ' ! not in field_map: %s'
    def getFieldData( me, fieldname, fielddata, do_err =True, d_default ={}):
        err = []
        try:
            d = me.field_map[ fieldname]      #global one - overrides local value'attributes
        except KeyError:
            e = me.ERR_not_in_fieldmap % fieldname
            err.append( e)
            if do_err:
                print(e)
            d = d_default
        value = me.get_value( fieldname, err, do_err)
        fielddata.setup( value= value, _model_context= me.model, **d)
        return err

from . import html

class UIController4HTML( UIController):
    if 0:
        from svd_util.fileCache import Descriptor4FileCachedLazyAsText
        class Descriptor4FileCachedLazyAsText( Descriptor4FileCachedLazyAsText):
            attrname = '_header_file'

    #name = 'pagename'
    header = ''     #str-format( title=, head_suffix=, body_suffix=)
    # e.g.
    # header = UIController4HTML.default_header
    # header = UIController4HTML.Descriptor4FileCachedLazyAsText( 'html/console_head.html', )
    html_layout = [ '' ]    #a static layout or a generating function, given ( fieldDataGetter)
    #field_map   = ...

    def __init__( me, *a,**k):
        UIController.__init__( me, *a,**k)
        me.header = html.Header( me.header, pagename= me.name )

    def redraw( me, html_layout =None, context =None, **ka_header):
        fieldDataGetter = me.getFieldData
        html_layout = html_layout or me.html_layout
        if callable( html_layout):
            r = html_layout( fieldDataGetter)
        else:
            r = html.TableHTML()
            r.all( html_layout, fieldDataGetter)

        focus = me.focus
        if focus:
            try: focus = r.focusmap[ focus ]
            except (AttributeError, KeyError): focus = None

        h = me.header.redraw( focus=focus,
                title= getattr( me.model, 'title',
                            getattr( r, 'title', '' )),
                **ka_header) #title, focus, ..

        h = me.fix_uribase_address( h, context)
        return h + html.unescape_lf( str(r) )

    def fix_uribase_address( me, hdr, context):
##  this forces html's base uri to end on /
#   as url/addr and url/addr/ are not treated same otherwise.
#   see comments near httpRequest.UI_HTTPRequestHandler.do_GET()
        if 1:
#        try:
            uri = getattr( me, 'uri', '')
            uri_base = getattr( context, 'uri_base', '')
#        except AttributeError: pass
#        else:
            if uri_base: uri_base+='/'
            if uri: uri+='/'
#            if callable( uri_base): uri_base = uri_base()
            hdr = hdr.replace( '</head>', '<base href="%(uri_base)s%(uri)s"> </head>' % locals() )
        return hdr

#.chooser, .text
    ui_css = """\
.checkbox, .button,
{
	cursor: pointer;
	cursor: hand;
	color: blue;
}

/* working here-there */
:focus  { outline: thick solid invert }
"""

    default_header = ("""\
<head>
<title> %(title)s </title>
""" + html.css_embed( ui_css) + """
%(head_suffix)s
</head>
<body %(body_suffix)s >
""")



########

if __name__ == '__main__':
    import sim
    console = sim.ui_html.ConsoleUIController( model=sim.models.console)
    print(console.redraw())

# vim:ts=4:sw=4:expandtab
