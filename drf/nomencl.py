from rest_framework import serializers
from rest_framework import viewsets
from django.http import Http404
from django.conf.urls import url
from svd_util.drf.fields import RelatedResourceUrlField

class nomencl_cfg:
    #inherit, setup these:
    view_base_name   = 'viewbasename'
    nomid__url_kwarg = 'somename'
    nomid__attr_access_via_instance = 'attrs.access.from.instance'
    api_viewset_single_nomencl      = r'vmrs-codekey/CK(?P<kcodekey>[0-9]+)'
    api_url_list_all_nomencl        = r'^vmrs-codekeys/'
    api_url_list_all_nomencl_name   = 'vmrs-codekey-list'

    #use these:
    @classmethod
    def nomid_url_kwarg_with_attr_access( me):
        return { me.nomid__url_kwarg: me.nomid__attr_access_via_instance }
    @classmethod
    def nomencl_url( me):
        'use in serlz:  url = this.nomencl_url()'
        return RelatedResourceUrlField( me.view_base_name+'-detail', pk= 'pk', **me.nomid_url_kwarg_with_attr_access())
    @classmethod
    def api_viewset4one( me, viewset):
        'use: router.register( *this.api_viewset4one())'
        return ( me.api_viewset_single_nomencl, viewset, me.view_base_name) #-> inomencl-list inomencl-detail ; url is relative!??

    @classmethod
    def nomencl_url4all( me, nomencl_fieldname):
        'use in serlz:  url = this.nomencl_url4all()'
        return RelatedResourceUrlField( me.view_base_name+'-list', get_attrib= get_item,
                **{ me.nomid__url_kwarg: nomencl_fieldname })
    @classmethod
    def api_url4all( me, view):
        'use: router.add_api_view( this.api_url4all())'
        return url( me.api_url_list_all_nomencl, view.as_view(), name= me.api_url_list_all_nomencl_name )

class Nomencl_Srlz4generic: #( serializers.ModelSerializer):
    'inherit and set Meta.model'
    if 0:
      class Meta:
        model = codes.BaseCode  #base-klas-of-all-nomenclatures
        exclude=()

    def get_fields(self):   #XXX HACK - doesnt want abstract models
        self.Meta.model._meta.abstract = False
        try:
            return super().get_fields()
        finally:
            self.Meta.model._meta.abstract = True

class Nomencl_ViewSet( viewsets.ReadOnlyModelViewSet):
    'inherit and set NOMENCL_CFG, serializer_class to child of Nomencl_Srlz4generic'
    NOMENCL_CFG = None #nomencl_cfg
    serializer_class = None #something inheriting Nomencl_Srlz4generic
    def _get_nomencl_model_by_url_kwarg( self, knomencl):
        raise NotImplementedError
        return nomencl_by_key.get( knomencl)
    def get_queryset( self):
        knomencl = self.kwargs[ self.NOMENCL_CFG.nomid__url_kwarg ]
        model = self._get_nomencl_model_by_url_kwarg( knomencl)
        if not model: raise Http404
        self._model = model     #HACK for get_serializer_class switch
        return model.objects.all()
    if 0:   #srlz switch: example
      def get_serializer_class( self):
        s = _overrides.get( self._model)
        if s: return s
        return super().get_serializer_class()


class HyperlinkedModelSrlz4nomenclatures_Mixin( object):
    ''' for models pointing to nomenclatures, this replaces nomenclature-links with RelatedResourceUrlField,
        because HyperlinkedRelatedField only has single getattr and one karg for reverse() regexp.
        depends on nomenclatures being accessible via common /view/nomenclname/ url
        depends on HyperlinkedModelSrlz_incl_excl_Mixin +related to add model-link-urls
        probably depends on HyperlinkedModelSerializer or similar to add nomencl's own .url
    '''
    #inherit and set NOMENCL_CFG, _is_nomencl_model
    NOMENCL_CFG = None #nomencl_cfg
    def _is_nomencl_model( self, m):
        raise NotImplementedError
        #return issubclass( m, codes.BaseCode)

    '''examples:
    dict(   view_base_name= 'inomencl-detail',
            knomencl = '__class__.__name__', )
     where:
        srlz.url = RelatedResourceUrlField( 'inomencl-detail', knomencl= '__class__.__name__', pk='pk' )
        api_viewsets = [ (r'nomencl/(?P<knomencl>[A-Z0-9_]+)', NomenclatureItemsViewSet, 'inomencl'), ]

    dict(   view_base_name= 'icodekey-detail',
            kcodekey = '__class__.KIND', )
     where:
        srlz.url = RelatedResourceUrlField( 'icodekey-detail', kcodekey= '__class__.KIND', pk='pk' )
        api_viewsets = [ (r'root-codekey/CK(?P<kcodekey>[0-9]+)', CodeItems_ViewSet, 'icodekey'), ]
    '''

    #this is called first
    def get_relation_kwargs( self, field_name, relation_info):
        model_field, related_model, to_many, to_field, has_through_model, reverse = relation_info
        if self._is_nomencl_model( related_model) and self.is_hyperlink( field_name):
            r = dict( self.NOMENCL_CFG.nomid_url_kwarg_with_attr_access(),
                        view_base_name= self.NOMENCL_CFG.view_base_name+'-detail',
                        source= None, )
            pk_name = serializers.HyperlinkedRelatedField.lookup_field
            r[ pk_name ] = pk_name
        else:
            r = super().get_relation_kwargs( field_name, relation_info)
        return r

    #serializer_related_field = RelatedResourceUrlField but only for nomenclatures
    def get_serializer_related_field( self, field_name, relation_info):
        f = super().get_serializer_related_field( field_name, relation_info)
        model_field, related_model, to_many, to_field, has_through_model, reverse = relation_info
        is_hyper = f is self.serializer_related_field
        if is_hyper and self._is_nomencl_model( related_model):
            f = RelatedResourceUrlField
        return f

#overall nomencl-list

from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from django.conf.urls import url
from svd_util.dicts import dictAttr
from svd_util.attr import get_item

if 0:
    class CodeUrl_Srlz( serializers.Serializer):
        'create such serlz'
        name = serializers.CharField()
        kind = serializers.CharField()
        url = nomencl_cfg.nomencl_url4all( nomencl_fieldname= 'kind')
        @classmethod
        def todata1( klas, model):
            return dictAttr( kind= str(model.KIND),     #ind='CK'+
                    name= model._meta.verbose_name if model.KIND<33000 else model.__name__
                   )
        @classmethod
        def todata( klas, request):
            all = request.query_params.get('all')      #HACK
            return [ klas.todata1( m) for m in codes.code_models if all or m.objects.exists() ]

class NomenclList_View( APIView ):
    'inherit and set above serlz1_class=above'
    SERLZ1_CLASS = None     #CodeUrl_Srlz
    def get( me, request, *args, **kwargs):
        #XXX if inheriting GenericAPIView*, this hits
        #   BrowsableAPIRenderer.get_filter_form - because of hasattr .queryset (=None)
        #   - which returns for non-list but does wrong stuff for lists..
        data = me.SERLZ1_CLASS.todata( request )
        serializer = me.SERLZ1_CLASS( many=True, data=data,
            context= GenericAPIView.get_serializer_context( me)
            )
        serializer.is_valid( raise_exception=True)
        return Response( serializer.data)

# vim:ts=4:sw=4:expandtab
