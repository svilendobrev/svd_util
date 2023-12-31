import six

from django import forms
from django.forms import BaseForm
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.db.models import ImageField
#from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib import admin

from ..attr import isiterable
from ..utils import get_attrib


class DisableDeleteAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(DisableDeleteAdminMixin, self).get_actions(request)
        actions.pop('delete_selected', None)
        return actions


def inline( bases, model, extra=0, verbose_name='', **kargs):
    data = dict(kargs,
            model = model,
            extra = extra,
            verbose_name = verbose_name,
            )
    if not isinstance(bases, tuple):
        bases = (bases,)
    return type('Inline', bases, data)


def make_image_tag(attr, short_description):
    def icon_tag(self, obj):
        value = get_attrib(obj, attr)
        if not value:
            return ''
        return mark_safe( u'<img src="%s" style="max-height: 30px"/>' % value.url)
    icon_tag.short_description = short_description
    return icon_tag


class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, **kwargs):
        output = []
        if value and getattr(value, "url", None):
            image_url = value.url
            file_name = str(value)
            output.append(u' <a href="%s" target="_blank"><img src="%s" alt="%s" style="max-height: 100px"/></a> %s ' % \
                          (image_url, image_url, file_name, _('Change:')))
        output.append(super(AdminFileWidget, self).render(name, value, attrs, **kwargs))

        output.append(u'<hr style="background:#ccc;">')
        #style="border: 0; height: 1px; background: #77B2D4; background-image: linear-gradient(to right, #ccc, #77B2D4, #ccc);">')
        return mark_safe(u''.join(output))


class SVGAndImageFormField( forms.FileField):
    def to_python( self, data):
        f = super().to_python( data)
        if f is None:
            return
        if not self.is_svg( f):
            raise forms.ValidationError( 'invalid svg image')
        f = data
        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)
        return f

    @staticmethod
    def is_svg( f):
        import xml.etree.ElementTree as et
        f.seek(0)
        try:
            for event, el in et.iterparse(f, ('start',)):
                if el.tag == '{http://www.w3.org/2000/svg}svg':
                    return True
        except et.ParseError: pass
        return False


class ImageAdminMixin:
    image_fields = None

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.get_image_fields():
            kwargs.pop('request', None)
            kwargs['widget'] = AdminImageWidget
            return db_field.formfield(**kwargs)
        return super(ImageAdminMixin, self).formfield_for_dbfield(db_field, **kwargs)

    def get_image_fields(self):
        if self.image_fields is None:
            return self._get_image_fields()
        return self.image_fields

    def _get_image_fields(self):
        return [
            f.name
            for f in self.model._meta.get_fields()
            if isinstance(f, ImageField)
        ]


class _RelatedFieldsButtons:
    ''' Mixin to control the appearance of add, change, delete buttons
    next to related fields in admin forms.

    # When your ModelAdmin or Form inherits this mixin you can e.g.:
    # hide all delete buttons by default:
    can_delete_related = False

    # show all "add" buttons by default:
    can_add_related = True

    # override defaults and customize certain fields:
    related_field_buttons = {
        'field_name1': {'add': True, 'change': False, 'delete': False},
         ...
        'field_nameN': {'add': False, 'change': True, 'delete': True},
    }
    '''
    can_add_related = False
    can_change_related = False
    can_delete_related = False
    related_field_buttons = {}

    def _setup_formfield(self, name, formfield):
        buttons = self.related_field_buttons.get(name, {})
        w = formfield.widget
        for mode in ('add', 'change', 'delete'):
            attr = 'can_%s_related' % mode
            value = buttons.get(mode, getattr(self, attr))
            setattr(w, attr, value)


class RelatedFieldsButtonsAdminMixin(_RelatedFieldsButtons):
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(RelatedFieldsButtonsAdminMixin, self
            ).formfield_for_dbfield(db_field, **kwargs
            )
        if formfield:
            self._setup_formfield(db_field.name, formfield)
        return formfield


class RelatedFieldsButtonsFormMixin(_RelatedFieldsButtons):
    def __init__(self, *a, **ka):
        super(RelatedFieldsButtonsFormMixin, self).__init__(*a, **ka)
        if isinstance(self, BaseForm):
            for name, field in self.base_fields.items():
                self._setup_formfield(name, field)


def is_popup(request):
    return IS_POPUP_VAR in request.GET


def _get_cleaner(form, field):
    def clean_field():
        return getattr(form.instance, field, None)
    return clean_field

class ReadOnlyFormMixin(forms.BaseForm):
    read_only = None
    def __init__(self, *args, **kwargs):
        super(ReadOnlyFormMixin, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            for name, field in six.iteritems(self.fields):
                if self.read_only is not None and name not in self.read_only:
                    continue
                field.widget.attrs['readonly'] = "readonly"
                field.disabled = True
                setattr(self, "clean_" + name, _get_cleaner(self, name))


class ReadOnlyAdminMixin:
    ''' useful when restricting add/edit/delete operations '''
    #add_form_template = change_form_template = 'read_only_form.html'
    readonly_inlines = True
    can_add = can_change = can_delete = False

    def zzget_form(self, request, obj=None, **kwargs):
        form = super(ReadOnlyAdminMixin, self).get_form(request, obj=obj, **kwargs)
        return type(form.__name__, (ReadOnlyFormMixin, form,), {})

    def has_add_permission(self, request, *args, **kwargs):
        return self.can_add and super().has_add_permission( request, *args, **kwargs)

    def has_change_permission(self, request, obj=None):
        return self.can_change and super().has_change_permission( request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        return self.can_delete and super().has_delete_permission( request, obj=obj)

    #def has_view_permission(self, request, obj=None):
    #    return True

    def get_inline_instances(self, request, obj=None):
        if self.readonly_inlines:
            new_inlines = []
            for cls in self.inlines:
                if not issubclass( cls, ReadOnlyInlineMixin):
                    cls = type(cls.__name__, (ReadOnlyInlineMixin, cls), {})
                new_inlines.append( cls)
            self.inlines = new_inlines
        return super().get_inline_instances( request, obj=obj)


class ReadOnlyInlineMixin( ReadOnlyAdminMixin):
    extra = 0


class ReadOnlyFieldsAdminMixin:
    ''' useful when only a few fields are read-only and all other are editable'''
    readonly_fields_in_add = ()
    readonly_fields_in_edit = ()

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields( request, obj=obj)
        add = obj is None
        t = type(fields)
        fields = list(fields)
        fields.extend( self.readonly_fields_in_add if add else self.readonly_fields_in_edit)
        return t(fields)


#XXX this has higher priority when used together with ReadOnlyFieldsAdminMixin
class EditableFieldsAdminMixin:
    ''' useful when only a few fields are editable and all other are read-only'''
    editable_fields_in_add = ()
    editable_fields_in_edit = ()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields( request, obj=obj)
        if getattr( self, 'editable_fields_admin_stop_recursion', None):
            return readonly_fields

        self.editable_fields_admin_stop_recursion = 1
        form = super()._get_form_for_get_fields(request, obj)
        fields = list(form.base_fields) + list(readonly_fields)
        self.editable_fields_admin_stop_recursion = 0

        add = obj is None
        exclude = self.editable_fields_in_add if add else self.editable_fields_in_edit
        fields = [f for f in fields if f not in exclude]
        return type(readonly_fields)(fields)


class RawIdFieldsAdminMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_id_fields = raw = list( self.raw_id_fields)
        for field in self.model._meta.get_fields():
            if isinstance( field, ( GenericForeignKey, GenericRelation)):
                continue
            if field.many_to_many or field.many_to_one:
                if field.name not in raw:
                    raw.append( field.name)


class SelectRelatedAdminMixin:
    '''speed up queries for populating form fields;
       for list view use ModelAdmin.list_select_related
    '''
    fields_select_related = {}   # field_name: (related_field1, related_field2...)
    fields_prefetch_related = {} # field_name: (prefetch_field1, prefetch_field2...)
    select_related = ()
    prefetch_related = ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.select_related is True:
            qs = qs.select_related()
        elif self.select_related:
            qs = qs.select_related(*self.select_related)
        return qs

    def get_field_queryset(self, db, db_field, request):
        qs = super().get_field_queryset(db, db_field, request)
        select_fields = self.fields_select_related.get(db_field.name)
        prefetch_fields = self.fields_prefetch_related.get(db_field.name)
        if select_fields or prefetch_fields:
            if qs is None:
                qs = db_field.remote_field.model._default_manager.using(db).all()
            if select_fields:
                if isinstance(select_fields, str):
                    select_fields = select_fields.split()
                qs = qs.select_related(*select_fields)
            if prefetch_fields:
                if isinstance(prefetch_fields, str):
                    prefetch_fields = prefetch_fields.split()
                qs = qs.prefetch_related(*prefetch_fields)
        return qs


class ExtraFieldsMixin:
    ''' useful for adding fields to various ModelAdmin field lists using mixins '''
    #### you can override any of these
    def readonly_fields_extra(self, request, obj=None):
        return []

    def list_display_extra(self, request):
        return []

    def list_filter_extra(self, request):
        return []

    def list_select_related_extra(self, request):
        return []

    def exclude_extra(self, request, obj=None):
        return []
    #############
    def get_readonly_fields(self, request, obj=None):
        return self.add_extra_fields( 'readonly_fields', request, obj=obj)

    def get_list_display(self, request):
        return self.add_extra_fields( 'list_display', request)

    def get_list_filter(self, request):
        return self.add_extra_fields( 'list_filter', request)

    def get_list_select_related(self, request):
        fields = super().get_list_select_related( request)
        if fields is False: # list_select_related takes boolean values too
            fields = []
        if not isiterable( fields):
            return fields
        extra = self.list_select_related_extra( request)
        return self._add_extra_fields( extra, fields)

    def get_exclude(self, request, obj=None):
        fields = super().get_exclude( request, obj=obj)
        extra = self.exclude_extra( request, obj=obj)
        if fields is None and extra:
            fields = self._add_extra_fields( extra, [])
        return fields

    def add_extra_fields(self, setting, *args, **kwargs):
        fields = getattr( super(), f'get_{setting}')( *args, **kwargs)
        extra = getattr(self, f'{setting}_extra')( *args, **kwargs)
        return self._add_extra_fields( extra, fields)

    def _add_extra_fields(self, extra, fields):
        t = type(fields)
        fields = list(fields)
        for name in extra:
            if name not in fields:
                fields.append( name)
        return t( fields)


class HelpersAdminMixin( ImageAdminMixin,
                        ExtraFieldsMixin,
                        ReadOnlyFieldsAdminMixin,
                        SelectRelatedAdminMixin,
                        RelatedFieldsButtonsAdminMixin,
                        ):
    pass

########

def admin_calc_field( list_display, **ka):
    def deco( f):
        for k,v in ka.items():
            setattr( f,k,v)
        f.admin_order_field = f.__name__
        list_display.append( f.__name__)
        return f
    return deco

def admin_register_from_model_resource( klas):
    '''@admin_register_from_model_resource
       class WhateverAdmin(ModelAdmin):
        class resource_class(ModelResource):
            class Meta: model = models.Whatever
    '''
    return admin.register( klas.resource_class.Meta.model )( klas)

def admin_register_making_model_resource( mymodel):
    'depends on import_export app'
    from import_export.resources import ModelResource
    class resource_class( ModelResource):
        class Meta: model = mymodel
    def admin_register_actual( klas):
        klas.resource_class = resource_class
        return admin.register( mymodel )( klas)
    return admin_register_actual


# vim:ts=4:sw=4:expandtab
