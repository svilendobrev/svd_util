# $Id: fielddata.py 8436 2009-04-27 09:46:29Z hristo $
#s.dobrev 2k4
# dialog/form layout description - field's meta-data

class FieldUndefinedError( LookupError): pass

class FieldData:
    address = '~address'
    value   = None
    #name   = '~name'
    readonly  = False
    #optional  = False
    immediate = True        #needs immediate server attention
    help = None
    #target = None           #frame-id to send form-result into
    label = None
    label_pos = 'default'   #default, before, after; None/empty???
    label_before = None
    label_after  = None

    def get_label_before( me, default =True, append =''):
        lp = me.label_pos
        return me.label_before or (
            lp=='before' or lp=='default' and default) and me.label+(
                    not me.label.endswith( append) and append or '') or ''
    def get_label_after( me, default =False):
        lp = me.label_pos
        return me.label_after or (lp=='after' or lp=='default' and default) and me.label or ''

    def __init__( me, field =None, **kargs):
        me.name = field
        me.address= field
        me.label= field
        me.value= None
        me.setup( **kargs)

    def setup( me, _model_context =None, **kargs):
        #for k,v in kargs.iteritems(): setattr( me, k, v)
        me.__dict__.update( kargs)

        if _model_context is not None:
            name = me.name
            for k,v in me.__dict__.items():
                if callable( v):
                    #print k,v, 'callable'
                    setattr( me, k, v( model=_model_context, name=name ) )

    def __str__( me):
        return '%s( %s) :%r' % (me.__class__.__name__, me.name, me.__dict__ )


class ChooserFieldData( FieldData):
    multiple  = False       #allows multiple choices
    value_range = ()        #range of possible values, e.g. list for choosers or ??
    value_if_not_in_range = None      #what to use when value is not in value_range
    height = 1

#TextFieldData:
#    height = 1         #>1 : textarea
#    width = 0          #default

# vim:ts=4:sw=4:expandtab

