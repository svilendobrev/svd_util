from rest_framework import serializers
''' usage of all things here is like:

class HyperlinkedModel_Srlz(
        srlzing.ModelSrlz_sorted_Mixin,
        hyperlink.HyperlinkedModelSrlz_hyper2_incl_excl_Mixin ,
        srlzing.ModelSrlz_subfields_Mixin,
        srlzing.ModelSrlz_addfields_Mixin,
        srlzing.ModelSrlz_renames_Mixin,
        srlzing.strname_Srlz_Mixin,
        hyperlink.HyperlinkedModelSerializer):
        ):
    pass
    #and exposed levers are:
    #
    #:from ModelSrlz_addfields_Mixin
    #   class Meta:
    #       addfields = list    #add-to-defaults
    #   meta_addfields = ...same
    #:from HyperlinkedModelSrlz_incl_excl_Mixin
    #   hyperlink_exclude = list-of-fieldnames
    #   hyperlink_include_only = list-of-fieldnames
    #   hyperlink_model2viewname = {model:viewname}    #overload viewname for reverse2url (the model.klasname.lower()+'-detail')
    #       viewnames can also be (view_name, dict( parent_lookup_<fname>: <field_id_attr>, .. pk='pk' )
    #       use on containers, with serializer_related_field = HyperlinkedRelatedField_Nested
    #   hyperlink_self_viewname  = viewname            #overload viewname for self.url reverse, has priority over above
    #       use on items, with serializer_related_field = HyperlinkedIdentityField_Nested
    #:from ModelSrlz_renames_Mixin
    #   serlz2model = {}
    #   serlz2model_ignore_missing = bool  #ignore non-existing field-names, default=False: die
    #   serlz2model_include_only   = bool  #ignore all non-mentioned field-names, default=False: use them too
    #:from ModelSrlz_sorted_Mixin
    #   sort_weights = {}  #fieldname: int

see also filters.FilterChoosableFields_ViewSet_Mixin

'''



class HyperlinkedModelSerializer( serializers.HyperlinkedModelSerializer):
    ''' Adds back pk field to the default fields (removed by orig HyperlinkedModelSerializer'''

    def get_default_field_names(self, declared_fields, model_info):
        names = super().get_default_field_names(
            declared_fields,
            model_info
        )
        names.insert(1, model_info.pk.name)
        return names

from svd_util.attr import get_attrib

class HyperlinkedRelatedField_Nested( serializers.HyperlinkedRelatedField):
    '''
    - get_attrib is overridable i.e. for multilevel dicts
    - lookup_attrs: { <urlkey>=<objattr>, .. }
    '''
    def __init__( self, **kwargs):
        self.lookup_attrs = kwargs.pop( 'lookup_attrs', None)
        self.get_attrib = kwargs.pop( 'get_attrib', get_attrib)
        super().__init__( **kwargs)
        if self.lookup_attrs is None:
            self.lookup_attrs = { self.lookup_field: self.lookup_url_kwarg }

    def get_object(self, view_name, view_args, view_kwargs):
        lookup_kwargs = {
            value_attr: view_kwargs[ urlkey]
            for urlkey, value_attr in self.lookup_attrs.items()
        }
        return self.get_queryset().get(**lookup_kwargs)

    def get_url(self, obj, view_name, request, format):
        #assert 0
        if hasattr(obj, 'pk') and obj.pk in (None, ''): return None

        kwargs = {
            urlkey: self.get_attrib( obj, value_attr)
            for urlkey, value_attr in self.lookup_attrs.items()
        }
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)

class HyperlinkedIdentityField_Nested( HyperlinkedRelatedField_Nested):
    def __init__( self, *a,**ka):
        ka.update( read_only = True, source = '*')
        super().__init__( *a,**ka)

class HyperlinkedModelSrlz_incl_excl_Mixin( object):
    '''usage: inherit, and in class:
    hyperlink_include_only = () #list of fieldnames
    hyperlink_exclude = () #list of fieldnames
    hyperlink_model2viewname = {model:viewname}     #overload viewname for reverse2url (the model.klasname.lower()+'-detail')
           viewnames can also be (view_name, dict( parent_lookup_<fname>: <field_id_attr>, .. pk='pk' )
           use on containers, with serializer_related_field = HyperlinkedRelatedField_Nested
    hyperlink_self_viewname  = viewname            #overload viewname for self.url reverse, has priority over above
           use on items, with serializer_url_field = HyperlinkedIdentityField_Nested

serializers.HyperlinkedModelSerializer uses default ModelSerializer machinery, setting in klas:
    serializer_related_field = HyperlinkedRelatedField
which is then to be used for each and every relation
and overrides get_default_field_names, hard-replacing model.pk.name with klas.url_field_name

default machinery is in klas.build_relational_field
it calls external get_relation_kwargs() which calls get_detail_view_name
which produces hardcoded viewname, and it happens very early

so this does:
 - control which fields to be hyperlinked:
        get_serializer_related_field()  - switches dynamicaly self.serializer_related_field between
        @(HyperlinkedModelSerializer) HyperlinkedRelatedField and (@ModelSerializer) PrimaryKeyRelatedField
 - control where to hyperlink to - (reverse()-related - viewname, args) etc:
        get_relation_kwargs() - which dynamicaly returns viewname/args as needed. the field_class is not known yet.
        fix_relation_kwargs() - needed to final tune field_kwargs for field_class (mostly removing extra stuff)
    Note: default HyperlinkedRelatedField can only handle one lookup_url_kwarg= getattr( obj, lookup_field)
        and is not readonly (hence all the machinery inside). Hence build_relational_field() is reworked below,
        use serializer_related_field= HyperlinkedRelatedField_Nested + hyperlink_model2viewname on containers
        use serializer_url_field = HyperlinkedIdentityField_Nested + hyperlink_self_viewname on items
'''
    #TODO -1 make above mixin
    # -2 one or other or both:
    #def get_default_field_names(self, declared_fields, model_info):
    #        [model_info.pk.name] +
    # vs
    #        [self.url_field_name] +
    # -3 for each hyper-field, have PrimaryKeyRelatedField or HyperlinkedRelatedField or both
    #

    def get_relation_kwargs( self, field_name, relation_info):
        return serializers.get_relation_kwargs( field_name, relation_info)

    hyperlink_include_only = () #list of fieldnames
    hyperlink_exclude = () #list of fieldnames

    def is_hyperlink( self, field_name):
        if self.hyperlink_include_only:
            hyper = field_name in self.hyperlink_include_only
        else:
            hyper = field_name not in self.hyperlink_exclude
        return hyper

    def get_serializer_related_field( self, field_name, relation_info):
        if self.is_hyperlink( field_name):
            return self.serializer_related_field
        return serializers.ModelSerializer.serializer_related_field
        #return self.serializer_related_field

    hyperlink_classes = ( serializers.HyperlinkedRelatedField, )
    def fix_relation_kwargs( self, field_class, field_kwargs):
        # `view_name` is only valid for hyperlinked relationships.
        if not issubclass( field_class, self.hyperlink_classes):
            field_kwargs.pop('view_name', None)

    #rework of ModelSerializer.build_relational_field. Changed: XXX
    # - get_relation_kwargs -> self.get_relation_kwargs()
    # - self.serializer_related_field -> self.get_serializer_related_field()
    # - pop(view_name) if not issubclass( HyperlinkedRelatedField) -> self.fix_relation_kwargs()
    # - view_name (for reverse of model) can be overloaded from hyperlink_model2viewname
    # - view_name (for reverse of self.url) can be overloaded from hyperlink_self_viewname or hyperlink_model2viewname

    hyperlink_model2viewname = {}
    def build_relational_field( self, field_name, relation_info):
        """
        Create fields for forward and reverse relationships.
        """
        field_kwargs = self.get_relation_kwargs( field_name, relation_info)

        to_field = field_kwargs.pop('to_field', None)
        if to_field and not relation_info.reverse and not relation_info.related_model._meta.get_field(to_field).primary_key:
            field_kwargs['slug_field'] = to_field
            field_class = self.serializer_related_to_field
        else:
            field_class = self.get_serializer_related_field( field_name, relation_info)

        self.fix_relation_kwargs( field_class, field_kwargs)    #fix kwargs as of field_class
        if 'view_name' in field_kwargs:
            relmodel = relation_info.related_model
            #relmodel = getattr( field_kwargs.get('queryset'), 'model', None)
            view_name = self.hyperlink_model2viewname.get( relmodel)
            if view_name:
                field_kwargs.update( self._view_name_with_lookup_attrs( view_name))

        return field_class, field_kwargs

    def _view_name_with_lookup_attrs( self, view_name):
        if isinstance( view_name, tuple):
            return dict( view_name= view_name[0], lookup_attrs= view_name[1])
        return dict( view_name= view_name )

    hyperlink_self_viewname = None
    def build_url_field( self, field_name, model_class):
        r = super().build_url_field( field_name, model_class)
        view_name = self.hyperlink_self_viewname or self.hyperlink_model2viewname.get( model_class)
        if not view_name: return r
        kargs = self._view_name_with_lookup_attrs( view_name)
        return (r[0], kargs)

if 0*'auto-strname-of-links':
    class StrName4id_asSerlzMethod( serializers.SerializerMethodField ):
        'usage: SField( fieldname)'
        def to_representation(self, value):
            #XXX result is None in query-lists ... needs prefetch
            return str( getattr( self.parent.instance, self.method_name, None))

from rest_framework.utils import model_meta
from .fields import RelatedResourceUrlField
from svd_util.django.models import get_field_multilevel

#TODO order of fields... now is url+id, normal model-fields, relations, url-ed fields..
#       -> url+id, sorted( modelfields -url,+url), sorted( relations)  - or url+id, sorted( all else)

class HyperlinkedModelSrlz_hyper2_incl_excl_Mixin(
        HyperlinkedModelSrlz_incl_excl_Mixin,  #full control of hyperlink-ing. Probably made partialy redundant by below
        ):
    '''
    NEEDS_URL, NEEDS_PK - not implemened, relying on HyperlinkedModelSerializer (org+drf) to do it
    NEEDS_HYPER2 - works
    maybe subset of all this will stay, to be decided later
    '''

    #viewname.. is autoguessed as class.lower()-detail
        #lookup_field = '__class__.__name__',   #these for HyperlinkedRelatedField but it only has getattr
        #lookup_url_kwarg = 'knomencl',

    NEEDS_URL = True
    NEEDS_PK  = True
    NEEDS_HYPER2= True

    _url_suffix = '_url'
    _pk_suffix  = '_pk'

    def get_fields(self):
        self.hyperlink_include_only = ['...'] # ~HACK dont hyperlink any
        fields = super().get_fields()
        del self.hyperlink_include_only
        if self.NEEDS_URL and self.url_field_name not in fields:
            pass #...
        if self.NEEDS_PK  and self.Meta.model._meta.pk.attname not in fields:
            pass #...
        info = model_meta.get_field_info( self.Meta.model)
        base_serializer_pk_field = serializers.ModelSerializer.serializer_related_field    #pk
        if self.NEEDS_HYPER2: #from already cooked links
            newfields = {}
            for fname,field in fields.items():
                if (isinstance( field, base_serializer_pk_field)
                    or isinstance( field, serializers.ManyRelatedField ) and isinstance( field.child_relation, base_serializer_pk_field)
                    ): #pk

                    mfield_name = field.source or fname
                    if not self.is_hyperlink( mfield_name): continue

                    #TODO if field=ManyRelatedField, use its .child_relation and create another
                    #   ManyRelatedField with child_relation= appropriate conversion (ser4pk->ser4url)
                    #   instead of converting field itself.
                    # Note: This is *hard* and fragile, may be no point trying again.

                    if mfield_name in info.relations:
                        relation_info = info.relations[ mfield_name]
                    else:
                        if isinstance( field, serializers.ManyRelatedField):
                            assert isinstance( field, serializers.ManyRelatedField), field
                            #hope for reverse generic = GenericRelation: -> ManyRelatedField
                            assert '.' not in mfield_name, mfield_name
                            #OK
                            rel = getattr( self.Meta.model, mfield_name).rel
                            relation_info = dict(   #see model_meta._get_reverse_relationships()
                                model_field= None,
                                related_model = rel.model,  #rel.model for @ManyToOneRel
                                to_many = True,
                                to_field = rel.target_field.name,
                                has_through_model=False,
                                reverse=True
                                )
                        else:
                            assert '.' in mfield_name, (mfield_name, field)
                            #OK

                            model1,mfname1 = get_field_multilevel( self.Meta.model, mfield_name)
                            minfo = model_meta.get_field_info( model1)
                            relation_info = minfo.relations[ mfname1 ]

                    if isinstance( relation_info, dict):
                        relation_info = model_meta.RelationInfo( **relation_info)
                    fklas, fkargs = self.build_relational_field( mfield_name, relation_info)

                    fkargs.update( source = mfield_name)
                    fname1 = fname + self._url_suffix
                    new_field = fklas( **fkargs)
                    new_field.read_only = True
                    newfields[ fname1] = new_field
                    if 0*'auto-strname-of-links':
                        newfields[ fname + '_str'] = StrName4id_asSerlzMethod( fname )

                elif isinstance( field, (serializers.HyperlinkedModelSerializer.serializer_related_field, RelatedResourceUrlField) ): #hyper
                    #this doesnt understand ManyRelatedField
                    mfield_name = field.source or fname
                    if mfield_name =='*': continue  #identity=self.url
                    relation_info = info.relations[ mfield_name]
                    self.hyperlink_exclude = [ mfield_name]     # ~HACK dont hyperlink it
                    fklas, fkargs = self.build_relational_field( mfield_name, relation_info)
                    del self.hyperlink_exclude
                    fkargs.update( source = mfield_name)
                    fname += self._pk_suffix
                    newfields[ fname] = fklas( **fkargs)
            fields.update( sorted( newfields.items()))

        return fields

# vim:ts=4:sw=4:expandtab
