from rest_framework import serializers

def raw_id_field(name, field_factory=None):
    '''
    Replaces a potentially huge select box in the browsable api with
    a simple input field
    '''
    if field_factory is None:
        field_factory = serializers.IntegerField
    return field_factory(
        source='%s_id' % name,
        style={'base_template': 'input.html', 'placeholder': ("%s ID" % name)}
    )


from rest_framework.reverse import reverse
from svd_util.attr import get_attrib

class RelatedResourceUrlField(serializers.Field):
    '''
    A read-only field that shows a url to a related resource
    to improve resource discoverability in the browsable api.
    To view the view_base_name and lookup_attrs user show_urls command.
    - get_attrib is overridable i.e. for multilevel dicts
    - lookup_attrs: { <urlkey>=<objattr> }
    - pass source=None to get usual pk/None handling (not called at all for None, else pk=obj.pk)
    - ALL url-regexp kwargs need be set via lookup_attrs
    '''
    def __init__(self, view_base_name=None, get_attrib =get_attrib, source='*', **lookup_attrs):
        self.view_base_name = view_base_name
        self.lookup_attrs = lookup_attrs
        self.get_attrib = get_attrib
        kargs = {}
        if source is not None:
            kargs.update( source=source)
        super().__init__(
            read_only=True,
            **kargs
        )

    def to_representation(self, value):
        kwargs = {
            key: self.get_attrib( value, value_attr)
            for key, value_attr in self.lookup_attrs.items()
        }
        context = self.context
        return reverse(
            self.view_base_name,
            request=context['request'],
            kwargs=kwargs,
            format=context.get('format')
        )


from collections import OrderedDict

class ChoiceField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        kwargs['choices'] = []
        super().__init__(**kwargs)

    def set_choices(self, choices):
        self.choices = choices
        self.grouped_choices = OrderedDict(self.choices)


class FilteredPrimaryKeyRelatedField( serializers.PrimaryKeyRelatedField):
    def __init__( me, *a, **ka):
        me.filter_func = ka.pop('filter_func', None)
        super().__init__( *a, **ka)
    def get_queryset( me):
        q = super().get_queryset()
        if callable( me.filter_func):
            q = me.filter_func( q, me.context)
        return q

__all__ = '''
    raw_id_field
    RelatedResourceUrlField
    ChoiceField
    FilteredPrimaryKeyRelatedField
'''.split()

# vim:ts=4:sw=4:expandtab
