#!/usr/bin/env python
# -*- coding: utf-8 -*-
#s.dobrev 2k4
from __future__ import print_function #,unicode_literals
'dialog/form layout auto-built from static_type'

from .layout import Panel
from svd_util.attr import get_attrib, issubclass

class _static_type:
    'default setup. may overwrite with your own BEFORE calling anything here'
    from static_type.types.base import StaticStruct, SubStruct
    from static_type.types.atomary import AKeyFromDict, Bool
    from static_type.types.sequence import Sequence

    AKeyFromDict.UI_type = '[? %s]'          #chooser direct
    #AKeyFromDict.UI_type = '[? %s_alt]'     #chooser_translated
    Bool.UI_type = '[_ %s]'          #checkbox
UI_type_default = '[ %s ]'       #text editor
#UI_type_default = '{ %s }'      #text label - or readonly text editor

# ok_butt = 'savebut'
# ok_label = 'savey'
#item = panel.Field( ok_butt, typ= 'button', width= 2+len( ok_label), fielddata=dict( label=ok_label, align='center' ) )


#_level=0
def _panel4any( **kargs):
    typ = kargs['typ']

#   global _level
#    print _level*'   ', '_panel4any', typ
    if issubclass( typ, _static_type.StaticStruct):
#        _level+=1
        make_panel = kargs['make_panel']
        p = make_panel( is_root= False, **kargs)
#        _level-=1
    elif isinstance( typ, _static_type.SubStruct):
        if kargs.pop( 'choosable', True):
            field_attrs = kargs.pop( 'field_attrs', {})
            field_attrs.update( choosable='button', readonly=True)
            p = panel4StaticType( field_attrs=field_attrs, **kargs)
        else:   #expanded
            p = make_panel4Struct( **kargs)
    elif isinstance( typ, _static_type.Sequence):
        p = panel4StaticSeq( **kargs)
    else: #plain atomary
        assert not getattr( typ, 'non_atomary', None)
        p = panel4StaticType( **kargs)

    return p

def panel4StaticType( typ, fullname, name_leaf, readonly =False, field_attrs =None, **kargs_ignore):
    txt = getattr( typ, 'UI_type', UI_type_default) % (fullname,)
    try: label_descr = typ.description
    except AttributeError: label_descr = None
    else: label_descr = label_descr()
    attrs = dict(
            label= name_leaf,   #+':',
            help = (getattr( typ, 'UI_type', None) and 'choose' or 'enter')+' '+name_leaf,
            value_range= getattr( typ, 'lister', ()),   # and typ.dict.keys() or (),
            readonly= readonly or getattr( typ, 'readonly', None),
            #valign ='top',
            #height ='value_range',  # generated as per lister
            width = min( 50, max( 15, getattr( typ, 'UI_width', None))),
        )
    if label_descr:
        attrs[ 'label_after'] = ' ('+label_descr+')'
    if field_attrs: attrs.update( field_attrs )
    field_map = { fullname: attrs }

    return txt, field_map


SEQ_IN_COLUMNS = 0 #!SEQ_IN_PANEL
def panel4StaticSeq( model, typ, fullname, name_leaf, readonly =False, **kargs):
    ''' this is for dynamic sequence-expansion/flattening'''
    #XXX this must to be remade! use a (list)browser + editor over a line in list

    if model is None:
        model = ()
        size = '<unknown>'
    else:
        size = len( model)
    title= name_leaf + '(%s)' % size

    _sync_masters = typ._sync_masters
    sizers = ''
    field_map = {}
    if typ.min != typ.max:
        if _sync_masters:
            sizers = ' [] size-sync to ' + ', '.join( [ m.name for m in _sync_masters] )
        if typ._sync_slaves or not _sync_masters:
            sizers = ' <incr>  <decr>' + sizers
            field_map[ 'incr'] = dict( address=fullname+'.incr', help= 'increase size by 1', label= 'append new item',  method='setvalue' )
            field_map[ 'decr'] = dict( address=fullname+'.decr', help= 'decrease size by 1', label= 'delete last item', method='setvalue' )
    if SEQ_IN_COLUMNS:
        txt = title
        title=None
    else:
        txt = ''
    panel = Panel( txt+ sizers, field_map,
            width=None,
            border=1,
            title=title
        )
    i=0
    for v in model:
        v_name = '[%(i)d]' % locals()
        v_fullname= '%(fullname)s.items.%(i)d' % locals()
        item_type = typ.item_type
        p = _panel4any( model=      v,
                        typ=        item_type,
                        name_leaf=  v_name,
                        fullname=   v_fullname,
                        readonly=   readonly,
                            #
                        field_attrs = dict( colspan ='all', ),
                        choosable = False,
                        **kargs
                )
#        if issubclass( item_type.typ, StaticStruct) or isinstance( item_type.typ, SubStruct):
#        elif isinstance( item_type, Sequence):
#       XXX ? why item_type.typ vs item_type above?

        panel += None   #new empty row
        if SEQ_IN_COLUMNS:
            panel *= None   # empty column? for pretty-view...
        panel *= p
        i+=1
    return panel

HIDE_OPTIONAL_OFF = True
def make_panel4Struct( **kargs):     #wrap or whatever
    return _make_panel4Struct( **kargs)

def _make_panel4Struct( model =None, typ =None, name_leaf =None, **kargs):
    assert typ is not None or model is not None
    if not typ: typ = model.__class__
    name = name_leaf
    if not name:
        try: name = typ.name
        except AttributeError: name = None
    if not isinstance( name, str): name = None
    title = name or typ.__name__
    panel = Panel()
    panel.header['title'] = title
    panel4Struct( panel=panel, model=model, typ=typ, **kargs)
    panel.generated = True
    return panel

def panel4Struct( panel, model, typ,
        name_leaf='',
        fullname ='',    #model's pfx/name in view
        readonly =False,
        is_root  =True,
        make_panel =make_panel4Struct,
        fields2ignore = None,
        extract_one_fld_panel = False,
        translator=None,
        attr_order=None,
        **kargs_ignore
    ):

    pfx = fullname and fullname+'.' or ''
    mtyp = typ
    attr_order = attr_order or list( mtyp._order_Statics(items=False))
    for name in attr_order:
        if fields2ignore and name in fields2ignore:
            continue
        typ = mtyp.StaticType[name]
        try:
            typ = typ.StaticType_alt
            fullname = pfx + typ.name
        except AttributeError:
            fullname = pfx + name

        if getattr( typ, 'meta', None): continue
        if getattr( typ, 'UI_hide', None): continue
        my_readonly = readonly
        optional = getattr( typ, 'optional', None)
        if optional:
            opt_name = optional.name
            on = get_attrib( model, opt_name, None)    #True - on by default
            item_name = not on and HIDE_OPTIONAL_OFF and name or '' #item's name at least
            opt_fullname = pfx+opt_name
            panel_opt = Panel( '[_ %(opt_fullname)s] %(item_name)s' % locals(),
                                { opt_fullname: dict( label='', width=30) },
                            )
            panel += panel_opt
            my_readonly = my_readonly or not on
            if not on and HIDE_OPTIONAL_OFF:      #without this, optional is visible but readonly
                continue
        m = None
        if getattr( typ, 'non_atomary', None): m = getattr( model, name, None)
        p = _panel4any( model= m,
                        typ  = typ,
                        fullname=   fullname,
                        readonly=   my_readonly,
                        name_leaf=  name,
                        make_panel= make_panel,
                        fields2ignore= fields2ignore,
                        translator= translator,
                )

        if translator:
            if isinstance( p, tuple):
                d = p[1]
                d = d[ list(d.keys())[0] ]
                l =  d.get('label')
                if l: d['label'] = translator(l)
            elif isinstance( p, Panel):
                p.header['title'] =  translator(p.header['title'])
        if not optional:
            panel += p
        else:
            if typ.non_atomary:
                panel_opt *= p
            else: #plain atomary
                txt,field_map = p
                panel_opt.field_map.update( field_map)
                panel_opt.parse( txt, start_new_row=False)

if __name__ == "__main__":
    import sys
    ms = []
    argv = sys.argv

    if not ms or 'all' in argv:
        from static_type.types.atomary import Text
        class Person( _static_type.StaticStruct):
            name = Text()
            sex  = Text( readonly= True, default_value ='yes')
        class MyDoc( _static_type.StaticStruct):
            person = Person()
            items = _static_type.Sequence( item_type=Text() )
            children = _static_type.Sequence( item_type=Person )
            note = Text( default_value='')

        d = MyDoc()
        d.person.name = 'HwiHwi'
        d.items.append( 'sofa' )
        d.items.append( 'divan' )
        d.items.append( 'boza' )
        c = Person()
        c.name = 'HwiHwi2'
        d.children.append( c )
        d.children.append( c )
        d.children.append( c )
        ms.append(d)

    for d in ms:
        panel = make_panel4Struct( model=d, fullname='doc' )
        print('=======')
        panel._print()

    if 'wx' in sys.argv:
        master = panel #Panel('@Edit Person')
        class Model:
            doc = d
        print(d)
        from myctl import MainController
        from wxmain import Frame
        ctl = MainController(Model)
        ctl.layout = master
        frame = Frame(ctl=ctl)

# vim:ts=4:sw=4:expandtab
