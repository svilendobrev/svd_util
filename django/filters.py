from __future__ import print_function #,unicode_literals

'''
XXX this works for django-filters 1.x. which relies on django < 2.1 .
not working for django-filters 2.0 which changed lots of names/things underneath.

usage:
1. either
add this to settings:
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
...

or set this to each view/viewsets with filters:
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)

2. if using FilterSet_addfields_labels_extras, import it then call FilterSet_addfields_labels_extras.fix_meta_options()
3. make base-filter class i.e. _FilterSet = FilterSet_addfields_labels_extras
4. probably will need this as base for all filter_class.Meta:
    class Meta4FilterSet:
        strict = django_filters.STRICTNESS.RAISE_VALIDATION_ERROR   # django_filters.STRICTNESS.IGNORE #default is somewhere in conf.settings
5. in each viewsets/, add such class inside:
    class filter_class( _FilterSet):
        class Meta( Meta4FilterSet):
            ...
        ...

'''
#XXX beware, django_filters is not the builtin django filters/forms, and not drf/filters
#XXX beware, django_filters.rest_framework.FilterSet is not django_filters.FilterSet
import django_filters

#XXX beware, rest_framework always uses all filter-backends in filter_queryset - regardless of view.action
def fix_filters_on_list_only():
    'also does fix_pass_view_to_filterset'
    if django_filters.rest_framework.DjangoFilterBackend.get_filter_class is get_filter_class1: return
    django_filters.rest_framework.DjangoFilterBackend._get_filter_class = django_filters.rest_framework.DjangoFilterBackend.get_filter_class
    django_filters.rest_framework.DjangoFilterBackend.get_filter_class = get_filter_class1
def get_filter_class1( self, view, queryset=None):
    if view.action != 'list': return
    fc = self._get_filter_class( view, queryset)
    if fc: fc.view = view
    return fc

def fix_pass_view_to_filterset():
    if django_filters.rest_framework.DjangoFilterBackend.get_filter_class in (get_filter_class1, get_filter_class2): return
    django_filters.rest_framework.DjangoFilterBackend._get_filter_class = django_filters.rest_framework.DjangoFilterBackend.get_filter_class
    django_filters.rest_framework.DjangoFilterBackend.get_filter_class = get_filter_class2
def get_filter_class2( self, view, queryset=None):
    fc = self._get_filter_class( view, queryset)
    if fc: fc.view = view
    return fc

########

class FilterSet_addfields_labels_extras( django_filters.rest_framework.FilterSet):
    ''' using the class Meta for:
        adding fields to default-list:
            addfields= [ name+ ] or dict( name: [lookup+])
        set labels per fieldname:
            field_labels= dict( name: label)
        set extra Filter-ctor-kargs per fieldname:
            field_extras= dict( name: dict( kargs) )

        beware: needs fix_meta_options()
    '''
    #addfields alternatives:
    # 1. use only .fields; if ALL_FIELDS in fields, add get_all_model_fields() to fields ... copypaste
    #+2. use new .addfields ; add those to fields .. copypaste
    # 3. make FilterSetOptions replace its own .fields, autoadding the get_all_model_fields if ALL_FIELDS .. no access to model
    # 4. if needed (ALL_FIELDS in fields or addfields), call original get_fields twice, replacing _meta.fields, then merge/join results

    _FilterSetOptions = django_filters.filterset.FilterSetOptions
    class FilterSetOptions( _FilterSetOptions):
        def __init__( self, options =None):
            super().__init__( options)
            self.addfields = getattr( options, 'addfields', None)
            self.field_labels = getattr( options, 'field_labels', None)
            self.field_extras = getattr( options, 'field_extras', None)
    @classmethod
    def fix_meta_options( klas):
        #....WTF Meta/class -> _meta/obj XXX HACKed, once
        if django_filters.filterset.FilterSetOptions is not klas.FilterSetOptions:
            django_filters.filterset.FilterSetOptions = klas.FilterSetOptions

    @classmethod
    def get_fields(cls):
        rfields = super().get_fields()   #original-only_fields-or-all
        addfields = cls._meta.addfields or ()
        if not addfields: return rfields
        #copy-paste from super.get_fields
        exclude = cls._meta.exclude or ()
        if not isinstance( addfields, dict):
            rfields.update( (f, ['exact']) for f in addfields if f not in exclude)
        else:
            rfields.update( (f, lookups) for f, lookups in addfields.items() if f not in exclude )
        return rfields

    @staticmethod
    def fields_with_lookups( fields, lookups= ['exact']): return [ (f, lookups) for f in fields ]

    if 0:
        #labels only
        @classmethod
        def filter_for_field(cls, f, name, lookup_expr='exact'):
            fr = super().filter_for_field( f, name, lookup_expr)
            if name in (cls._meta.field_labels or ()):
                fr.label = cls._meta.field_labels[ name ]
            return fr
    else:
        #labels + extras
        @classmethod
        def filter_for_lookup(cls, f, lookup_type):
            filter_class, params = super().filter_for_lookup(f, lookup_type)
            if f.name in (cls._meta.field_labels or ()):
                params.update( label = cls._meta.field_labels[ f.name ] )
            if f.name in (cls._meta.field_extras or ()):
                params.update( cls._meta.field_extras[ f.name ] )
            return filter_class, params



#######

import django_filters.constants

class OrderingFilter_with_default_adding_id( django_filters.OrderingFilter):
    'default=<list-of-fieldnames> ; or =__all__ meaning all given fields, in their order'
    def __init__( self, *a, **ka):
        self.default = ka.pop( 'default', None)
        with_id = self.with_id = ka.pop( 'with_id', 'id')
        fields = ka.pop('fields', {})
        if self.default == '__all__':
            self.default = list( fields)
        fields = self.normalize_fields(fields)
        if with_id and with_id not in fields:
            fields[ with_id ] = with_id
        super().__init__( fields=fields, *a, **ka)
    def filter( self, qs, value):
        if value in django_filters.constants.EMPTY_VALUES and self.default: value = self.default
        if self.with_id and self.with_id not in value:
            value = list( value) + [ self.with_id ]
        return super().filter( qs, value)

#######

import django.forms

'''for filter which is on by default:
x=..Filter(..)
x.filter() is not called at all if (cleaned) value is None - see FilterSet.qs() ;
so, cleaned value should never be None, then .filter/method is called -> do whatever
(i.e. err=incl/excl/all are the 3 choices, and None converts into one of them)
cleaning is in field.clean/field.to_python (form.Field*).. i.e.
    a) override thatFilter.thatField's clean()
 or b) class Meta: form = MyForm # inherit forms.Form and
        ba) override overall MyForm.clean(), about that particular fieldname / after field.clean()
     or bb) having MyForm.clean_<fieldname>() / after field.clean()
most forms.*Fields.to_python( value=empty_values) return None, some do '', [], die, etc
'''
#b)
#class myForm( forms.Form):
#    def clean_autho( self, value):
#        if value is None: return

#a)
class DefaultChoiceField( django_filters.ChoiceFilter.field_class): #django.forms.ChoiceField):
    def __init__( me, **ka):
        me.default_choice = ka.pop( 'default_choice', None)
        super().__init__( **ka)
        if me.default_choice is not None:    #XXX use =None -> original behaviour
            assert me.valid_value( me.default_choice), ( me.default_choice, me.choices)
    def to_python( me, value):
        if value in me.empty_values: return me.default_choice
        return super().to_python( value)

class ChoiceFilter_all_only_none( django_filters.ChoiceFilter):
    field_class = DefaultChoiceField
    _any = 'any'
    _choices = [ _any ] + 'only none'.split()
    def __init__( me,
            filter      = {},       #kargs-dict() or tuple(args,kargs) or callable( me,query)-returning-dict-or-tuple
            filter_is_in= False,    #"only .errors" -> errors!=None -> filter_is_out ; "only x>5" -> x__gt=5 -> filter_is_in
            incl_method = 'filter', #methodname on query, or callable( me, query)-returning query or callable( ***filter_args)
            excl_method = 'exclude',#methodname on query, or callable( me, query)-returning query or callable( ***filter_args)
            default_choice  = _any, #one of _choices; #XXX =None -> original behaviour
            labels = {},            #{choice:label} choice from _choices; defaults to themselves
            empty_label ='default', #label of 'default' option
            distinct    = False,
            #label = 'is exported',
            **ka):

        assert default_choice is None or default_choice in me._choices, default_choice
        me.filter_args = filter
        me.incl_method = incl_method
        me.excl_method = excl_method
        me.filter_is_in = filter_is_in
        super().__init__( null_label = None,
            default_choice = default_choice,
            empty_label   = empty_label,
            choices = [ (k,labels.get(k,k)) for k in me._choices ],
            #name=name,     #uses .filter_args instead
            #method = ..    #uses .filter() instead
            **ka)
    def filter( me, qs, value):
        if value == me._any: return qs
        logic = value == 'only'     #positive logic, filter_in
        if not me.filter_is_in: logic = not logic
        method = me.incl_method if logic else me.excl_method
        if isinstance( method, str):
            qs = getattr( qs, method)   #->callable( ***filter_args)
        else:
            qs = method( me, qs)        #->result or callable( ***filter_args)
        if callable( qs):
            fargs = me.filter_args
            if callable( fargs): fargs = fargs( me, qs)
            if isinstance( fargs, dict): fargs = (),fargs
            else: assert isinstance( fargs, tuple) and len(fargs)==2, fargs
            a,ka = fargs
            qs = qs( *a,**ka)
        if me.distinct: qs = qs.distinct()
        return qs


import django_filters.fields
class ModelChoiceIterator( django_filters.fields.ModelChoiceIterator):
    '''apply limit_choices_to on choice-fields=queryset (i.e. relation) in the filter-forms
        and if just int, force [:limit] on query.. enhancing limit_choices_to :P

    either assign limit_choices_to on filterfield, or using FilterSet_addfields_labels_extras:
    class Meta:
        field_extras = dict( thefieldname= dict( limit_choices_to=200))
    '''
    #__init__ is called *before* field.limit_choices_to is set... so dynamic:
    def _get_queryset( me):
        q = me._queryset
        limit = me.field.get_limit_choices_to()
        if isinstance( limit, int):
            q = q[ :limit]
        elif limit:
            q = q.complex_filter( limit)
        return q
    def _set_queryset( me,q): me._queryset = q
    queryset = property( _get_queryset, _set_queryset)

def fix_allow_limit_choices_on_filter():
    django_filters.fields.ModelChoiceField.iterator = ModelChoiceIterator

#########

class FilterChoosableFields_ViewSet_Mixin:
    '''filter for choosing the subset of output serializer fields, i.e. the "columns" dimension.
    use: inherit this in some viewset
         add the filter using this.setup_rfields_choices*()
    '''
    _rfields = None
    def get_serializer( me, *a,**ka):
        serializer = super().get_serializer( *a,**ka)
        if me._rfields:
            srfields = serializer.child.fields
            for k in list( srfields):
                if k not in me._rfields: del srfields[k]
            me._rfields = None
        return serializer

    def filter_queryset( me, queryset):
        #obtain _rfields from queryset (set there by filter), save it for get_serializer
        queryset = super().filter_queryset( queryset)
        me._rfields = getattr( queryset, '_rfields', None)
        return queryset

    @classmethod
    def setup_rfields_choices( klas, keyvalue_list, label ='output fields'):
        rfields = django_filters.MultipleChoiceFilter( label= label, field_name=None,
            choices = keyvalue_list,
            method = klas.filter_by_rfields,
            )
        rfields.always_filter = False
        return rfields
        if 0:
            rfields = django_filters.CharFilter( label= 'output fields', field_name=None,
                        method= lambda sq,field_name,value: qs.values( *value.split()))
    @staticmethod
    def filter_by_rfields( qs, field_name, value):
        qs._rfields = value
        return qs #.values( *value)

    @classmethod
    def setup_rfields_choices_from_serializer( klas, serlz_klas, **ka):
        return klas.setup_rfields_choices( [ (f.field_name, f.field_name) for f in serlz_klas()._readable_fields ], **ka)

__all__ = '''
    FilterSet_addfields_labels_extras
    OrderingFilter_with_default_adding_id
    ChoiceFilter_all_only_none
    fix_allow_limit_choices_on_filter
'''.split()

# vim:ts=4:sw=4:expandtab
