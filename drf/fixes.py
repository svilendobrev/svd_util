
from rest_framework import renderers, fields, serializers

#HACK "enforce consistent style" bullshit. тея даже си вярват
_bind1 = fields.Field.bind
def bind1(self, field_name, parent):
    if self.source == field_name: self.source = None
    return _bind1( self, field_name, parent)
_bind2 = fields.SerializerMethodField.bind
def bind2(self, field_name, parent):
    if self.method_name == 'get_'+field_name: self.method_name = None
    return _bind2( self, field_name, parent)
def fix_bind_pedantry():
    ''' allow specifing same source=name as fieldname
        allow specifing same method_name=..name as get_..name
    '''
    if fields.Field.bind is not bind1:
        fields.Field.bind = bind1
    if fields.SerializerMethodField.bind is not bind2:
        fields.SerializerMethodField.bind = bind2

######

#HACK  do not render NullBooleanField as text
_map_bool2text = fields.to_choices_dict( [ ('True', 'yes'), ('False', 'no'), ])
def iter_options(self): return fields.iter_options( _map_bool2text,)
def fix_NullBooleanField_becoming_text():
    if getattr( serializers.NullBooleanField, 'iter_options', None) is iter_options: return
    renderers.HTMLFormRenderer.default_style.mapping[ serializers.NullBooleanField ] = dict( base_template= 'select.html' ) # select.html or radio.html
    serializers.NullBooleanField.iter_options = iter_options
    #serializers.NullBooleanField.choices = property( lambda self: _map_bool2text ) for radio.html

if 0:   # XXX noooo, this turns False into  checked in BooleanField XXX FIXME
    #HACK  do not render False as '' ; str(value)
    def as_form_field(self):
        value = '' if (self.value is None) else str(self.value)
        return self.__class__(self._field, value, self.errors, self._prefix)
    def fix_False_becoming_emptytext():
        from rest_framework.utils.serializer_helpers import BoundField
        if BoundField.as_form_field is as_form_field: return
        BoundField.as_form_field = as_form_field

######
#WTF BoundField.as_form_field: None -> "" screws all nulls XXX
#either use below NullCharField or CharField( allow_blank=False, allow_null=True) relying on fields.Field.get_value logic
class NullCharField( fields.CharField):
    'empty "" -> None'
    def to_internal_value( me, value):
        assert me.allow_null
        assert me.parent.Meta.model._meta.get_field( me.field_name).null
        return super().to_internal_value( value) or None

if 0: # see glueing for thise
    _get_declared_fields = serializers.SerializerMetaclass._get_declared_fields
    def fix_serlz_order_inheritance():
        if serializers.SerializerMetaclass._get_declared_fields is not _get_declared_fields: return
        #HACKfix XXX - works only for serlzs declared after this  (also see below alternative ..)
        serializers.SerializerMetaclass._get_declared_fields = lambda bases, attrs: _get_declared_fields( tuple(reversed(bases)), attrs)


def build_field( self, field_name, info, model_class, nested_depth):
    r = self._mybuild_field( field_name, info, model_class, nested_depth)
    if field_name not in info.fields_and_pk and field_name in info.relations and not nested_depth and info.relations[ field_name].reverse :
        klas,kwargs = r
        remote_field = model_class._meta.get_field( field_name).remote_field
        if remote_field.many_to_many and remote_field.blank:
            kwargs[ 'required'] = False
    return r
def fix_many2many_reverse_blank_required():
    if serializers.ModelSerializer.build_field is not build_field:
        serializers.ModelSerializer._mybuild_field = serializers.ModelSerializer.build_field
        serializers.ModelSerializer.build_field = build_field


def fix_drf_all():
    fix_bind_pedantry()
    fix_NullBooleanField_becoming_text()
    fix_many2many_reverse_blank_required()
#    fix_False_becoming_emptytext()
    #NullCharField

__all__ = '''
    fix_bind_pedantry
    fix_NullBooleanField_becoming_text
    fix_False_becoming_emptytext
    NullCharField
'''.split()

# vim:ts=4:sw=4:expandtab
