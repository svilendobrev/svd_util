# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals

from common_helpers.dicts import dictAttr
from collections import OrderedDict as dictOrder
# from pprint import pprint, PrettyPrinter
# PrettyPrinter._dispatch[dictOrder.__repr__] = PrettyPrinter._dispatch[dict.__repr__]

class Gen_DRF:
    def setup( me):
        super().setup()
        me.setup_serlzs()
        me.setup_filters()

    def setup_serlzs( me):
        'all drf stuff - here'
        #me.link_type = 'integer'    #for each ForeignKey... whatever it is

        #TODO differ object's primarykey from any other link
        #TODO walk nested/sub-viewsets i.e. /deal/x/items/y/

        from rest_framework import serializers
        from common_helpers import drf

        me.cfg_templates( fieldklas2template = {    #order does matter, first may win!
            serializers.DateTimeField: 'datetime',
            serializers.DateField:     'date',
            serializers.NullBooleanField: 'onoff',
            serializers.BooleanField: 'onoff',
            serializers.IntegerField: 'number',
            serializers.CharField:    'text',
            #serializers.PrimaryKeyRelatedField: 'link',
            serializers.SerializerMethodField:  'text',
            serializers.ReadOnlyField:  'text',
            serializers.MultipleChoiceField: 'multichoice',
            serializers.ChoiceField:    'choice',
            serializers.FileField: 'file',
            })
        me._cfg.fieldklasi4url = [
            drf.RelatedResourceUrlField,
            serializers.HyperlinkedRelatedField,
            ]
        #_cfg.fieldklasi4bool = [ drf_fields.BooleanField ] + api.BooleanField4nomencl.__subclasses__() #: checkbox,

        me.cfg_templates( fieldklasi4link = {
            serializers.PrimaryKeyRelatedField: 'link',
            serializers.ManyRelatedField:   dict( f= 'link', many=True),   #error_fields, treatments, item_fields
            serializers.Serializer: 'object',   #subserializers
            })

    def setup_filters( me):
        #me._cfg.filterklas2template = {}

        import django_filters as df
        me._cfg.baseFilter = df.Filter
        if 0:
          me.cfg_templates( fieldklas2template = {
            df.IsoDateTimeFilter: 'datetime',
            df.DateFilter:     'date',
            #df.DateFromToRangeFilter XXX
            #df.RangeFilter XXX
            df.BooleanFilter: 'onoff',
            #common_helpers.django.filters.ChoiceFilter_all_only_none XXX
            df.NumberFilter: 'number',
            df.CharFilter:    'text',
            df.ModelChoiceFilter: 'link',
            df.ModelMultipleChoiceFilter: dict( f='link', many=True),
            df.MultipleChoiceFilter: 'multichoice',
            df.ChoiceFilter:    'choice',
            })
        dff = df.filters
        import django.forms.fields as ff
        if 1:
          me.cfg_templates( fieldklas2template = {
            dff.IsoDateTimeField: 'datetime',
            ff.DateField:     'date',
            #ff.DateRangeField XXX  = from df.DateFromToRangeFilter
            #ff.RangeField  XXX     = from df.RangeFilter
            ff.NullBooleanField: 'onoff',
            ff.DecimalField: 'number',
            ff.CharField:    'text',
            #df.MultipleChoiceFilter: 'multichoice',
            dff.ChoiceField:    'choice',
            })
          me.cfg_templates( fieldklasi4link = {
            dff.ModelChoiceField: 'link',
            dff.ModelMultipleChoiceField: dict( f='link', many=True),
            })

    def field2child_if_many( me, field, schema):
        from rest_framework import serializers
        return isinstance( field, serializers.ListSerializer) and field.child

    def field2model_field( me, field, schema):
        f = field   #serlz-field
        #if isinstance( f, tuple( me._cfg.fieldklasi4url)): return link2url( f)

        mname = getattr( f, 'source', None) or f.field_name
        if not mname or mname == '*': return #??? serlzMethod

        if me.ctx.get( 'filter'):#, isinstance( f, me._cfg.get( 'baseFilter')):
            model = me.ctx.model
        else:
            model = f.parent.Meta.model

        mnames = mname.split('.')
        for mname in mnames[:-1]:
            rel = getattr( model, mname ).field.rel
            model = rel.model
        try:
            return model._meta.get_field( mnames[-1])
        except me._cfg.FieldDoesNotExist:
            return

    def field2choices( me, field):
        choices = field.choices
        return [ (list(x) if isinstance(x,tuple) else x)
                for x in (choices.items() if isinstance( choices, dict) else choices)
                ]

    def fields_no_urls( me, fields):
        return dict( (name,f) for name,f in fields.items()
                if not name.endswith('_url') and not isinstance( f, tuple( me._cfg.fieldklasi4url))
                )
    def fields_no_readwriteonly( me, fields):
        return dict( (name,f) for name,f in fields.items()
                if not (f.read_only if me.EDITOR else f.write_only)
                )
    def get_conf_serlzs( me, viewset, suburl):
        return [ dictAttr(
                    serklas = viewset.serializer_class,
                    resource = suburl,
                    resource_name= suburl, # + (not me.EDITOR) * '_list',
                    # switching serializer_class has no Meta; switching viewset has no queryset
                    model   = getattr( viewset.serializer_class, 'Meta', viewset.queryset ).model,
                    #all else goes into conf
        # viewset: readonly   -> form: readonly
        # viewset: writable   -> form: writable unless dynamicaly checkable for readonly per-instance
        #writable = callable( getattr( viewset, 'update', None))
        #writable= jstr4bool( writable)
                    )]

        #sfull = getattr( viewset, 'serializer_class_list_full', None)
        #if sfull: return dict( list_full = sfull )
    def serklas2fields( me, serklas, viewset, model):
        return serklas().fields

        if 0: #polymorphic-all-in-one from .srlzs
            fields = {}
            for s in serklas.srlzs.values():
                fields.update( s.fields )
            fields.update( serklas().fields)
            return fields

    def strctx( me):
        return  ' '.join( [me.ctx.viewset.__qualname__, me.ctx.serklas.__qualname__, me.ctx.resource_name ])

    def config4vs( me, viewset, suburl ):
        r = dictOrder()
        for rsrlz in me.get_conf_serlzs( viewset, suburl):
            #if not serklas: continue    #let extra_conf_serlzs kill list= if needed
            serklas = rsrlz.pop( 'serklas')
            model   = rsrlz.pop( 'model')
            resource_name = rsrlz[ 'resource_name']
            me.ctx = dictAttr( viewset= viewset, resource_name= resource_name, serklas= serklas, model= model )
            fields = me.serklas2fields( serklas, viewset, model)
            fields = me.fields_no_urls( fields)
            fields = me.fields_no_readwriteonly( fields)

            c = r[ resource_name ] = me.conf( fields,
                                    type = model.__name__,
                                    **rsrlz     #all goes in
                                    )

            if me.EDITOR: continue
            filter_class = getattr( me.ctx.viewset(), 'filter_class', None)
            if not filter_class: continue
            filts = dict( filter_class.base_filters )  ## .base_filters >= .declared_filters

            #name=order? or issubclass( type, OrderingFilter XXX
            order = filts.pop( 'order', None)
            if order:
                c['orderby'] = [ (c if c[0] != '-' else c[1:] + '__desc') for c,l in order.extra['choices'] ]

            f = me.make_gform()
            f.ctx = dictAttr( me.ctx, filter= True, serklas= filter_class, )
            for k,flt in filts.items():
                field = filts[ k] = flt.field
                field.field_name = flt.field_name   #copy, can be None
            rf = f.schema_for_fields( filts )
            if rf: c[ 'filter'] = rf

        return r

    def _gen_cfgs_from_viewsets( me, api_viewsets, **ka):
        for suburl,vs in api_viewsets:
            yield me.config4vs( vs, suburl, **ka)

    def vs_is_readonly( me, vs):
        from rest_framework import viewsets, routers
        #HACK
        m2a = {}
        for r in routers.SimpleRouter.routes:
            m2a.update( getattr( r, 'mapping', {} ).items())
        a2m = dict( (v,k) for k,v in m2a.items())

        def vs_has_method( view, method):
            return method in view.http_method_names and hasattr( view, method)
        def vs_has_action( view, action):
            return action in a2m and hasattr( view, action) and a2m[action] in view.http_method_names

        return ( issubclass( vs, viewsets.ReadOnlyModelViewSet) and all(
                    [ not vs_has_method( vs, m) for m in 'put post patch'.split() ]
                  + [ not vs_has_action( vs, a) for a in 'create update'.split() ]
                ))
        #writable = callable( getattr( viewset, 'update', None))



# vim:ts=4:sw=4:expandtab
