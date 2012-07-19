# $Id: html.py,v 1.39 2007-07-12 16:25:20 niki Exp $
#s.dobrev 2k3-4

_USE_HIDDEN_address = 1
_USE_HIDDEN_method  = 2
USE_HIDDEN = _USE_HIDDEN_address

#uri: <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
##   method_name/field_path?value=$value    no USE_HIDDEN /separate_address
##or method_name?field_path=$value          USE_HIDDEN /separate_address
##or field_path?method_name=$value          USE_HIDDEN /separate_method

from svd_util.url import urlparse, query2dict #, dict2query, #unquote, quote
from svd_util.htmlcodec import htmlcodec, lf2br, escape_lf, unescape_lf, wrap_pre
def htmlize(v):
    return htmlcodec.encode( str(v))

#turn linebreaks into <br>+linebreak
def htmlize_br( v):
    return lf2br( htmlize( v))

#escape_lf - turn linebreaks into escaped-linebreak - to be able to diff
#between linebreak in text and and linebreak in html-structure;

def htmlize_lf( v):
    return escape_lf( htmlize( v))

def uri2fieldMethod( uri, use_separate =None, urlparse =urlparse):
    if use_separate is None: use_separate = USE_HIDDEN
    if isinstance( uri, str): u = urlparse( uri)
    else: u = uri
    path, params, query, fragment = u
    if query and query[0]=='?': query = query[1:]
    path = path.strip( '/')     #del head and trail /
    pathsplit = path.split( '/')
    address = method = ''
    querymap = query2dict( query)
    if querymap:
        if use_separate == _USE_HIDDEN_address:
            method = pathsplit.pop(-1)
            address = querymap[ 'fid']
        elif use_separate == _USE_HIDDEN_method:
            address = pathsplit.pop(-1)
            method = querymap[ 'method']
        querymap.setdefault( 'value', None)
    #print path, querymap, use_separate
    if not use_separate:
        try:
            method, address = pathsplit[:2]
        except ValueError:  #not found -> single result returned
            raise KeyError, (path,'',querymap)
        else: del pathsplit[:2]
    path = '/'.join( pathsplit)
    return path, address, method, querymap

def fieldMethod2uri( address, method, use_separate =None):
    if use_separate is None: use_separate = USE_HIDDEN
    method  = str( method)
    address = str( address)
    separates = {}
    if use_separate == _USE_HIDDEN_address:
        uri = method
        separates['fid'] = address
    elif use_separate == _USE_HIDDEN_method:
        uri = address
        separates['method'] = method
    else:
        uri = method + '/' + address
        address = method = ''
    return uri, separates

def script_link( filename):
    return '<script LANGUAGE="javascript" SRC="%s"> </script>' % filename
def script_embed( txt):
    return '\n'.join( ('<script LANGUAGE="javascript">', txt, '</script>' ))
def css_link( filename):
    return '<link REL="STYLESHEET" TYPE="text/css" HREF="%s" >' % filename
def css_embed( txt):
    return '\n'.join( ('<style TYPE="text/css"><!--', txt, '--></style>') )

##################
### each iframe needs own .css and .js inside its document

# context-help:
#  - call via onMouseOver//onMouseOut or onFocus//onBlur or separate image/button/link//click-in-it
#  - show on statusline, and or baloon-like (popup) - see millstone  showPopupById/hidePopupById
#  - <.... title=context-help-text-here ...>

#dialog-like window:
# w.menubar.visible=false;
# w.toolbar.visible=false;
# w.locationbar.visible=false;
# w.personalbar.visible=false;
# w.scrollbars.visible=false;
### w.statusbar.visible=false;

# message-box dialog: window.alert()
# ok/cancel dialog: window.confirm()

# all submits should either go to other window/form, so current field doesn't lose focus,
# or current (new) focus should be submit-ed, and then re-focused on re-load
# e.g. <form .. target=listener_window ..> - but it will get the focus?

#focusing:
# You can give focus to a window programmatically by giving focus to an object in the window
# or by specifying the window as the target of a hypertext link

#field state:
# modified  : <input .. onchange="this.className='modified' ..>
# focused   : <input .. onfocus="this.className='focused' ..>

def makefid( field):
# dont use id(field) direct: f-1234 (id= -1234) is not valid javascript name!
    fid = str(id(field))
    fid = fid[0]=='-' and 'm'+fid[1:] or fid
    return 'f_' + fid

class formElement:
    def __init__( me, form_id ='', elem_id =''):
        me.formname = me._makeAddress( form_id, 'forms')
        me.elemname = me._makeAddress( elem_id, 'elements')
    def address( me):
        return me.formname+'.'+me.elemname
    #def docAddress( me): return 'document.'+me.address()
    #def docFocus( me): return me.docAddress()+'.focus()'

        #javascript absolute scoping: document.form.element
        #   form = formname or 'forms'[index]
        #   element = elementname or 'elements'[index]
    def _makeAddress( me, id, array_name):
        if not id: id = 0
        if type( id) is type( '' ):
            return id
        return '%s[%d]' % (array_name, id)

default_form_element = formElement()

class Header:
    header = '<body %(body_suffix)s >\n'
    body_suffix = """
 onLoad="document.%(focus)s.focus()"
 onFocus="top.document.title=document.title"
"""
    def __init__( me, header ='', pagename =''):
        me.header = header or me.header
        me.pagename = pagename

    def closewindow( me ):
        return '<html>\n'+ script_embed( 'window.close();' )
    def redraw( me, focus =None, pagename ='', title ='', head_suffix ='', body_suffix =''):
        if not pagename: pagename = me.pagename
        if not title: title = 'title?'+pagename

        if not focus:
            focus = default_form_element.address()
        body_suffix += me.body_suffix % locals()
        if 0:
            body_suffix += ('\n zonFocus="alert( \'%s focused\')"' % pagename)

        r = me.header % locals()
        return '<html>\n'+ r + script_embed( """\
formlast='';
function onfocus_h( fdaddr ) {
    if (formlast != '') {
        formlast.next_adr.value=fdaddr;
        formlast.submit();
    } formlast='';
}

function click_event(e) {
//    alert( 'click '+(formlast==''?'':formlast.fid.value));
    onfocus_h( '');
    return true;
}
window.onclick=click_event;
//document.onclick=click_event;

function blur_event(e) {
    window.status='';
    return true;
}
window.onblur=blur_event;

""" )

def comment( s):
    return '<!-- '+s+' -->'
onPFX = '\n      '
#def onEvent( evt, x): return 'on'+evt+'="'+x+'"'
for evt in ('onChange', 'onClick', 'onBlur', 'onFocus', 'onMouseOver', 'onMouseOut'):
    exec """def %(evt)s(x, ret=True): return onPFX+'%(evt)s="'+x+'; return '+(ret and 'true' or 'false')+'"' """ % locals()


def back2future( fdaddr =None):
    if fdaddr is None: return ''
    return "onfocus_h( '"+fdaddr+"');\n"


def helpStatusLine( fdhelp, fdaddr =None):
    return onFocus( back2future( fdaddr) +
                    (fdhelp and 'window.status=\'' +fdhelp+ '\';' or '')
           ) #+ (fdhelp and onBlur( 'window.status=\'\';') or '')
    #window.defaultStatus is what's shown otherwise

def helpStatusLineMouse( fdhelp):
    return (fdhelp and
                onMouseOver( 'window.status=\'' +fdhelp+ '\';') +
                onMouseOut ( 'window.status=\'\';') +
            '' or '')
    #window.defaultStatus is what's shown otherwise

def separatesAsHidden( separates):
    return ''.join( [ '\n   <input type=hidden name="%s" value="%s">' % keyvalue
                    for keyvalue in separates.iteritems() ] )
            #(separate_address and
            #    ' <input type=hidden name="fid" value="' +separate_address +'"> \n' or '') +

 #both div class=, form class=, assume whole_ table cell; so put style-class here:
def labelWrapOpen( label, style):
    return ( '\n   <nobr class="'+ style +'"> '+ label )
def labelWrapClose( label):
    return ( label + '\n   </nobr> ')

#########



class formpack( formElement):
    def __init__( me, formname, action, body ='', target ='', onsubmit =''):
        formElement.__init__( me, formname, 0)      #active element is #0
        me.action = action
        me.body = body
        me.target = target
#        me.onsubmit = onsubmit
    def __str__( me):       #immediate
        return (
            '<form name="%(formname)s" action="%(action)s"'+
            (me.target and ' target="%(target)s"' or '') +
#            (me.onsubmit and ' onsubmit="%(onsubmit)s"' or '') +
            '>'+
            '\n %(body)s '+
            '\n <input type=hidden name="next_adr" value="">' +
            #'\n <input type=hidden name="next_value" value="">' +
            '\n</form>\n'
            ) % me.__dict__

from fielddata import FieldData #, ChooserFieldData, FieldUndefinedError

def Button( fd):
    field = fd.name
    formname = makefid( field)
    action, separates = fieldMethod2uri( fd.address, getattr( fd, 'method', 'push'))
    label = fd.label or field
    return formpack( formname, action,
                ' <input type=submit' +
                    ' class="button"' +
                    ' value="' +htmlize_lf( label)+ '"'+
                    #' name="' +fd.address +'"'+
                    #onClick( 'this.form.submit()' )+
                    helpStatusLine( fd.help, fd.address ) +
                ' >' + separatesAsHidden( separates) +
                '', target=getattr( fd, 'target', None),
#                    onsubmit=getattr( fd, 'onsubmit', None),
             )

def toggleCheckbox_by_id( fieldid):
    return  'toggleCheckbox(\''+fieldid+'\');'       #see ui.js
def toggleCheckbox( field):
    return field+'.checked = !'+field+'.checked;'

GO_PREV = 0

def futbut( form):
    return 0*(" if (formlast != '') {" + (
  GO_PREV and """\
    %(form)s.prev_adr=formlast.fid.value;
    %(form)s.prev_value=formlast.value.value;
""" or """\
    formlast.next_adr.value=%(form)s.fid.value;
    formlast.next_value.value=%(form)s.value.value;
    formlast.submit();
""") + '}') + ' %(form)s.submit();' % locals()

def Checkbox_labeler( label, fd, formname):
    return label and (
            '\n    <span ' +
                #'class="checkbox" ' +    #inherits nobr/div one
                    onChange(
                        toggleCheckbox( formname+'.elements[0]' ) +
                        #toggleCheckbox_by_id( fieldname) +
                        (fd.immediate and futbut( formname) or '') +
                    '') +
                '\n    >' +
                htmlize_br( label) +
            '</span>'
        ) or ''

def Checkbox( fd):
    field = fd.name
    formname = makefid(field)
    action, separates = fieldMethod2uri( fd.address, 'setvalue')

    #submit() sends 'action?name=value' only if checked; else, sends empty 'action?'
    #so, name/address should be in the action, e.g.
    #   ->True: set/$fid?value=True        ->False: set/$fid?
    #or, name/address should be in hidden input (only within separate form!). e.g.
    #   ->True set?fid=$fid&value=True     ->False: set?fid=$fid
    #or, onClick should not do submit at all - e.g. window.location=$action?$fid=checkbox.value

    l_b = fd.get_label_before( default=False)   #always wrap chkbox with label, default= after
    l_a = fd.get_label_after(  default=True)
    return formpack( formname, action,
            labelWrapOpen( Checkbox_labeler( l_b, fd, formname), 'checkbox') +
            '\n    <input type=checkbox' +      #must be first element - see toggleCheckbox() below
                    ' class="checkbox"' +
                    #' id=' +str(fieldname) +
                    ' name="value"'+
                    ' value="1"'+   #True
                    (fd.value     and ' checked'  or '') +      #="True"
                    (fd.readonly  and ' disabled' or '') +      #+' readonly'
                    (fd.immediate and onChange( futbut( 'this.form') ) or '') +
                    helpStatusLine( fd.help, fd.address ) +
                ' >' +
            labelWrapClose( Checkbox_labeler( l_a, fd, formname) ) +
            separatesAsHidden( separates) +
            '', target=getattr( fd, 'target', None) )

class ChooserShort( formpack):  #( ChooserFieldData):      #known-size: drop-down-list or list-box
    def __init__( me, fielddata):
        #me.fd = ChooserFieldData( **fielddata.__dict__)     #?needed
        me.fd = fielddata

        fd = me.fd
        options = fd.value_range and me.options( fd.value_range)
        if not options:
            me.formname = ''
            return

        field = fd.name
        formname = makefid(field)
        action, separates = fieldMethod2uri( fd.address, 'setvalue')

        fdheight = getattr( fd, 'height', 0)
        if fdheight < 0:  #means auto-as-value_range
            fdheight = min( -fdheight, len( options) )
        #if fdheight == 'value_range':  #means auto-as-value_range
        #    fdheight = len( options)
        formpack.__init__( me,
                    formname, action,
                    labelWrapOpen( htmlize_br( fd.get_label_before( append=':') ), 'chooser') +
                    '\n    <select' +
                        ' class="chooser"' +
                        (fdheight and ' size='+str(fdheight) or '') +
                        #' id=' +str(fieldname) +
                        #' name="'+ (separate_address or 'value') +'"'+     #ok for address only
                        ' name="value"'+
                        (fd.readonly  and ' disabled' or '') +      #+' readonly'
                        (fd.multiple  and ' multiple' or '') +
                        (fd.immediate and onChange( 'formlast=this.form') or '') +
                        helpStatusLine( fd.help, fd.address ) +
                        ' >' +
                        '\n     '.join( ['']+options)+
                    '\n    </select>' +
                    labelWrapClose( htmlize_br( fd.get_label_after() )) +
                    separatesAsHidden( separates) +
                '', target=getattr( fd, 'target', None) )


        #value_range: sequence of items - all should be different;
        # item can be value or tuple( value, text)
    def options( me, value_range):
        fd = me.fd
        #no subvalues/optgroup's
        current = fd.value
        if not fd.multiple:
            current_ = current is not None and ( current ,) or ()
        r = []
        n_selected = 0
        value_if_not_in_range = fd.value_if_not_in_range    #should be a value_range's attribute
        valid_value_if_not_in_range = False
        for v in value_range:
            if type( v ) is type( () ):
                v, v_text = v
                has_text = True
            else:
                v_text = v
                has_text = False
            selected_v = v in current_
            selected_if_not_in_range = v == value_if_not_in_range
            valid_value_if_not_in_range += selected_if_not_in_range
            selected = selected_v or selected_if_not_in_range
            selected = selected and ' selected' or ''
            n_selected += bool( selected_v)
            r.append(
                '<option' +
                    selected +
                    (has_text and ' value="'+htmlize_lf(v)+'"' or '') +
                    ' >' +
                    htmlize( v_text ) +        #no linebreaks here!
                '</option>'
                )
        if not n_selected and current:
            if value_if_not_in_range is None or not valid_value_if_not_in_range:
                print '! field', fd.name, ': value not in range: "%(current)s" not in %(value_range)s' % locals()
        return r

    def __str__( me):
        if not me.formname:      #nothing to choose from
            if getattr( me.fd, 'hide_if_empty', 0):
                return ''
            return '! '+me.fd.name+': nothing to choose from'
            #return comment( err)
        return formpack.__str__( me)

#class ChooserLong( ChooserFieldData):       #unknown size - e.g. directory
# use iframe + separate url = iterator over options

def TextInput( fd):     #text-line or text-area
    #def __str__( fd):
        field = fd.name
        formname = makefid(field)
        action, separates = fieldMethod2uri( fd.address, 'setvalue')

        fdheight = getattr( fd, 'height', 0)
        fdwidth  = getattr( fd, 'width',  0)
        if fdheight>1:
            ttypeOpen = ('\n    <textarea' +
                            ' rows='+str(fdheight)+
                            (fdwidth>0 and ' cols='+str(fdwidth) or '')
                        )
            #nothing extra between <textarea>...</textarea> !!!
            ttypeClose= '\n   >'+htmlize_lf( fd.value)+ '</textarea>'
        else:
            ttypeOpen = ('\n    <input type=text' +
                            (fdwidth>0 and ' size='+str(fdwidth) or '')
                        )
            ttypeClose= '\n   value="'+htmlize_lf( fd.value) +'">'

        return formpack( formname, action,
                    labelWrapOpen( htmlize_br( fd.get_label_before( append=':') ), 'text') +
                        ttypeOpen+
                        ' class="text"' +
                        #' id=' +str(fieldname) +
                        ' name="value"'+
                        (fd.readonly  and ' disabled' or '') +      #+' readonly'
                        #(fd.immediate and onChange( 'this.form.submit()') or '') +
                        (fd.immediate and onChange( 'formlast=this.form') or '') +
                        helpStatusLine( fd.help, fd.address ) +
                        ttypeClose+
                    labelWrapClose( htmlize_br( fd.get_label_after() )) +
                    separatesAsHidden( separates) +
                '', target=getattr( fd, 'target', None) )

def TextLabel( fd):   #( FieldData):     #text-label - readonly, no actions
    #def __str__( fd):
        field = fd.name
        #label = fd.label_pos is not None and fd.label or ''
        pre = getattr( fd, 'pre', None)
        r = '<nobr class=textlabel'+ helpStatusLineMouse( fd.help)+ '\n  >'
        r += htmlize_br( fd.get_label_before( append=':') ) +' '
        ## XXX ?whatabout <br> in <nobr> ?
        if pre:
            r+= wrap_pre( htmlize_lf( fd.value))
        else:
            r+= htmlize_br( fd.value)
        r+= htmlize_br( fd.get_label_after() )
        r+= '</nobr>\n'
        return r

def TextOutside( fd):                   #text-label - readonly, no actions, part of template
    return htmlize_br( fd.label)


#################

_factories = {}
for b in [ 'Button', 'Checkbox', 'ChooserShort', 'TextInput', 'TextLabel' ]:
    _factories[b] = _factories[ b.lower() ] = eval( b)
_factories[ 'Chooser']  = ChooserShort
_factories[ 'Text']     = TextInput
_factories[ 'Label']    = TextLabel
_factories[ 'Outside']  = TextOutside
for b,f in _factories.items():
    _factories[ b.lower() ] = f


class TableHTML:
    config__no_factories = False
    def __init__( me, fieldDataGetter =None, out =None, pfx =''):    #out should define += operator
        me.fieldDataGetter = fieldDataGetter
        me.out = out or ''
        me._col = 0
        me._row = 0
        me.max_columns = 0
        me._level = 0
        me.pfx = pfx

    def pfx_level( me): return me.pfx + '  '*me._level

    def all( me, description, fieldDataGetter =None):
        me.fieldDataGetter = fieldDataGetter
        me.head( layout= description[0] )
        for row in description[ me.use_layout:]:
            me.row( row)
        me.tail()
        return me.out

    headers = { 'width': '100%',
                'cellspacing': None, 'cellpadding': None,
                'frame': None, 'border': None, 'rules': None,
                'height': None,
                }
    def head( me, max_columns =0, layout =None, **kargs_header):
        if not layout or type(layout[0]) != type({}):
            layout = None
        else: max_columns = len(layout)
        me.max_columns = max_columns
        me.layout = layout
        me.use_layout = bool(layout)
        me._row = 0

        html = '\n'+ me.pfx_level() + '<table '
        for k,v in me.headers.iteritems():
            v = kargs_header.get( k,v )
            if v is not None:
                html += ' %s="%s"' % (k,str(v))
        html += '>\n'
        me.out += html

    def row( me, row):
        me.row_head( row)
        if row:
            for c in row:
                me.cell( c)
    def row_head( me, row, align =''):
        me._row += 1
        me._col = 0
        max_columns = me.max_columns
        me._level = 1
        html = me.pfx_level() +'<tr'
        me._level += 1
        if align:  html += ' align='+align
        html += '>\n'

        if not row and max_columns>1:      #empty row
            html += me.pfx_level()+ '<td colspan=%d>\n' % max_columns
        me.out += html

    def cell_head( me, align= '', valign= '', colspan= 1, width ='', rowspan= 1, **k_ignore):
        col = me._col
        me._col += 1
        me._level = 2
        html = me.pfx_level() + '<td'
        if me.use_layout and me._row==1:
            for key_value in me.layout[ col].iteritems():
                html += ' %s=%s' % key_value
        if width:  html += ' width='+width
        if align:  html += ' align='+align
        if valign: html += ' valign='+valign
        if colspan not in (1, None):
            if colspan in (0, 'all'):
                colspan = me.max_columns
            html += ' colspan='+str(colspan)
        if rowspan not in (11,None, 0,'all'):
            #if colspan in (0, 'all'):
            #    colspan = me.max_columns
            html += ' rowspan='+str(rowspan)
        html += '>\n'
        me.out += html
        me._level +=1

    def cell( me, entry):
        me.cell_head()
        me.cell_body( entry)

    def cell_body( me, entry):
        if entry:
            r = entry
            if type( entry) != type('') and not me.config__no_factories:
                if isinstance( entry, FieldData):
                    factory = entry.factory
                    field = entry.name
                    fielddata = entry
                else:
                    factory, field = entry
                    fielddata = None

                factory = _factories.get( factory, None)
                if factory:
                    fd = fielddata or FieldData( field)       #default
                    if me.fieldDataGetter:
                        err = me.fieldDataGetter( field, fd, do_err=not fielddata)   #override?
                    r = factory( fd)
                    try:
                        #me.out.map( fd.name, r.address() )
                        me.out.map( fd.address, r.address() )
                    except AttributeError: pass
            html = str( r)
        else:
            html = comment( 'empty entry')
        html = me.pfx_level() + html.replace( '\n', '\n'+ me.pfx_level() )
        html += '\n'
        me.out += html

    def tail( me):
        me._level = 0
        html = me.pfx_level() + '</table> \n'
        me.out += html



if __name__ == '__main__':
    import unittest
    from svd_util.testeng.func import myTestCase4Function
    from svd_util.mix import Namer
    class myTestCase4Function( myTestCase4Function, unittest.TestCase):
        def do( me, value, expect):
            return uri2fieldMethod( value, use_separate=me.use_separate )[1:]    #less url)

    class test_uri2fieldMethod( unittest.TestCase):
        def test_something( me): pass       #needed to get call()ed!
        def __call__( me, result):
            title = me.__class__.__name__
            result.stream.writeln( title)

            r_none = ('','',{})
            for k,v in {
                None:{
                    '/'                 :r_none,
                    'some/path'         :r_none,
                    '/some/root/path'   :r_none,
                    },
                0:{
                    '/setv/my.name?value=T'     :('my.name', 'setv', {'value': 'T'}),
                    '/setv/my.name?'            :('my.name', 'setv', {}),
                    '/setv/my.name'             :('my.name', 'setv', {}),
                    },
                Namer( '_USE_HIDDEN_address', globals()):{
                    '/setv?value=T&fid=my.name' :('my.name', 'setv', {'fid': 'my.name', 'value': 'T'}),
                    'setv?value=T&fid=my.name'  :('my.name', 'setv', {'fid': 'my.name', 'value': 'T'}),
                    '/setv?fid=my.name'         :('my.name', 'setv', {'fid': 'my.name', 'value': None}),
                    },
                Namer( '_USE_HIDDEN_method', globals()):{
                    'my.name?value=T&method=setv'   :('my.name', 'setv', {'method': 'setv', 'value': 'T'}),
                    'my.name?method=setv'           :('my.name', 'setv', {'method': 'setv', 'value': None}),
                    },
                }.items():
                    for value,res in v.items():
                        c = myTestCase4Function.setup( value=value, expect=res,
                                name = ' ( %(k)s, %(value)r )' % locals() )
                        c.use_separate = getattr( k, 'value', k)
                        c(result)

    def test_htmlTable():
        print 'htmlTable..'
        from sim.ui_html import console
        layout = console.html_layout_txt
        #h1 = html_table( layout)
        #print h1, '---------'
        t = TableHTML()
        t.all( layout)
        h2 = t.out
        print h2
        print '---------'
        #from svd_util.diff import diff
        #diff( h1,h2, 'html_table', t.__class__.__name__)

    #test_htmlTable()
    unittest.main()

# vim:ts=4:sw=4:expandtab

