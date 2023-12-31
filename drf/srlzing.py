
from collections import OrderedDict
from rest_framework.fields import get_attribute     #like get_attr/get_item++

def get_instance_data_from_serializer( serializer, writable =True):
    'comparable to .validated_data'
    inst = serializer.instance
    fs = serializer._writable_fields if writable else serializer._readable_fields
    return OrderedDict(
                (f.source, get_attribute( inst, f.source_attrs) )
                for f in fs
                )

class ModelSrlz_renames_Mixin( object):
    '''list with renames for Serializer ; uses whatever available fields.
    does not really need a ModelSerializer
    applies after exclude
    beware of inheritance order.. probably after HyperlinkedModelSrlz_hyper2_incl_excl_Mixin
    '''
    serlz2model = dict(
        # serlz_fieldname = 'model_fieldname', #expects model_fieldname to be there already
        #...
    )
    serlz2model_ignore_missing  = False  #ignore non-existing field-names, default=False: die
    serlz2model_include_only    = False  #ignore non-mentioned field-names, default=False: use them all

    def get_fields(self):
        fields = super().get_fields()
        if not self.serlz2model:
            if self.serlz2model_include_only: fields.clear()
            return fields
        to_del = set()
        if self.serlz2model_include_only:
            to_del.update( set(fields) - set( self.serlz2model) )
        for sfname, mfname in self.serlz2model.items():
            if mfname not in fields:
                if self.serlz2model_ignore_missing: continue
                assert mfname in fields, (mfname,self)
            f = fields[ sfname] = fields[ mfname]
            if not f.source:
                f.source = mfname
            to_del.add( mfname)
        for mfname in to_del:
            fields.pop( mfname, None)
        return fields

class ModelSrlz_renames_autoadd_Mixin( ModelSrlz_renames_Mixin):
    'also try autoadd non-declared but used in serlz2model model-fields'
    def get_field_names(self, declared_fields, info):
        return list( super().get_field_names( declared_fields, info )) + [
            m for s,m in self.serlz2model.items() if m not in declared_fields
            ]

class ModelSrlz_addfields_Mixin( object):
    ''' to add to the default fields, use one or more of:
           Meta.addfields       =list-of-names
           class.meta_addfields =list-of-names
           self._meta_addfields() method (returning list-of-names)
    '''

    def get_default_field_names(self, declared_fields, model_info):
        names = super().get_default_field_names( declared_fields, model_info)
        names.extend( getattr( self.Meta, 'addfields', ()))
        names.extend( getattr( self, 'meta_addfields', ()))
        names.extend( self._meta_addfields())
        return names

    def _meta_addfields(self): return ()

from rest_framework.utils import model_meta
from svd_util.django.models import get_field_multilevel

class ModelSrlz_subfields_Mixin( object):
    ''' allow "somerel.somefield" in Meta.fields or Meta.addfields'''

    def build_field(self, field_name, info, model, nested_depth):
        if '.' in field_name:
            model,field_name = get_field_multilevel( model, field_name)
            info = model_meta.get_field_info( model)
        return super().build_field( field_name, info, model, nested_depth)

class ModelSrlz_sorted_Mixin( object):
    'pk, url if any, then all the rest, sorted according to weights[name]+name, default weight=0'
    _pk_name = 'id'
    sort_weights = None     #so viewset.serializer_class.update( ...) fails
    def get_fields(self):
        fields = super().get_fields()
        r = OrderedDict( (k,fields[k]) for k in [
                self._pk_name,    #self.Meta.model._meta.pk.name, -- wrong on inheriting models
                getattr( self, 'url_field_name', None),
                ] if k in fields)
        sort_weights = self.sort_weights or {}
        url_suffix = getattr( self, '_url_suffix', '') or '_url'
        def keyer( kv):
            name = k = kv[0]
            if name.endswith( url_suffix): name = name[ :-len(url_suffix)] + '_' + url_suffix   #-> x, x_url, x_aa, x_aa_url, x_bb ..
            return (sort_weights.get( k, 0), name)
        r.update( sorted( fields.items(), key = keyer))
        return r

from rest_framework import serializers
class strname_Srlz_Mixin( serializers.Serializer):  #Serializer not object, else strname is not inherited visible
    strname = serializers.SerializerMethodField()
    def get_strname( self, obj): return str( obj)


class BelongsTo_parent_Mixin( object):
    parent_id_name      = None
    parent_lookup_name  = None

    def create( self, validated_data):
        data = dict(validated_data)
        k,v = self.get_parent_name_value()
        data[ k] = v
        return super().create( data)

    def get_parent_name_value( self):
        parent_context = self.context['view'].get_parents_query_dict()
        return self.parent_id_name, int(parent_context[ self.parent_lookup_name])
        #XXX or maybe this?
        c = parent_context.get( self.parent_lookup_name)
        return int(c) if c else None


__all__ = '''
    get_instance_data_from_serializer
    ModelSrlz_renames_Mixin
    ModelSrlz_renames_autoadd_Mixin
    ModelSrlz_addfields_Mixin
    ModelSrlz_subfields_Mixin
    ModelSrlz_sorted_Mixin
    strname_Srlz_Mixin
    BelongsTo_parent_Mixin
'''.split()

# vim:ts=4:sw=4:expandtab
