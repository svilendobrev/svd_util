#TODO
# -- DjangoDebug: tuned off. too unreliable, does not count in nested namespaces but noises same not-happened get() n-times..
# -- annotate :   no, means dynamic schema. Expose named hardcoded queries where needed
# + expose q_* methods as data-getters    - inefficient for all(), optimize with (optional) annotate
# + polymorphism - Asset -> Interface ; as Union cannot have fields (real or calc)
# + relations in data: field(filter)
#   + rel _count _all_count

###########

WRAP_TYPE = 'w_'    #prefix for classes, if any
WRAP_TYPE_ONLY = True and WRAP_TYPE
#POLYMORPHIC_AS_UNION = False  #Union cannot have fields apart of automatic __typename

from collections import defaultdict
import graphene
from graphene_django import DjangoObjectType

from .base import   oregistry, change_frozen_meta, Resolver, id2obj, metainfo_put
from .filter import model_filter as _model_filter, make_inmodel, _ftypes, make_filter, is_rel_tomany

_query = {}
_types = {}     #? same as oregistry.get_type_for_model
_query2model = {}
#also see filter._ftypes
_types4filter = _ftypes     #backward compatibility

from django.core.exceptions import FieldDoesNotExist
def make_one( model, ql_model, resolver_kargs ={}):
    pkarg = model._meta.pk.name
    #WTF.. in polymorphism pk is named <base>_ptr
    if pkarg.endswith('_ptr'):
        try:
            pkarg = model._meta.get_field('id').name
        except: pass
    return graphene.Field( ql_model, #id= graphene.ID(),
            **{ pkarg: graphene.ID() },
            resolver= Resolver( lambda ctx, **ka: id2obj( model, ka[ pkarg], **resolver_kargs)
            ))

def pslots( x): return ', '.join( k+'= '+ str(getattr( x, k)) for k in x.__class__.__slots__)
#ctx['info'] = ResolveInfo
#ResolveInfo.operation = OperationDefinition
#OperationDefinition.selection_set = SelectionSet
#SelectionSet.selection_set = SelectionSet | None

def make_all( model, ql_model =None, ql_inmodel =None, model_filter =_model_filter, resolver_kargs ={}, **ka):
    if not ql_model: ql_model = _types[ model]
    if not ql_inmodel: ql_inmodel = _ftypes[ model]
    return graphene.List( ql_model,
            resolver= Resolver( lambda ctx, **kargs: model_filter( model, kargs, ctx=ctx ), **resolver_kargs ),
            **make_filter( ql_inmodel),
            **ka)
def _query_or_model( model, attr, root):
    if not (attr and root): return model
    q = getattr( root, attr)
    qall = getattr( q, 'all', None)
    if callable(qall): return qall()    #relation/query
    return q()  #just method

def make_count( model, ql_inmodel =None, attr =None, model_filter =_model_filter, resolver_kargs ={}):
    if not ql_inmodel: ql_inmodel = _ftypes[ model]
    return graphene.Int(
            resolver= Resolver( lambda ctx, **kargs: model_filter(
                            _query_or_model( model, attr, ctx.root),
                            kargs, parent=ctx.root, ctx=ctx ).count(),
                        **resolver_kargs),
            **make_filter( ql_inmodel or _ftypes[ model], pagination= False))
_allcnt = {}
def make_all_count( model, ql_model =None, ql_inmodel =None, attr =None, model_filter= _model_filter, resolver_kargs ={}):
    if not ql_model: ql_model = _types[ model]
    if not ql_inmodel: ql_inmodel = _ftypes[ model]
    modelname = ql_model.__name__   #model.__name__
    if model not in _allcnt:
        _allcnt[ model] = type( 'all_count_'+ modelname, (graphene.ObjectType,) , dict(
            data    = graphene.List( ql_model),
            count   = graphene.Int(),
            export_url = graphene.String(),
            ))
    o_all_count = _allcnt[ model]
    return graphene.Field( o_all_count,
            resolver= Resolver( lambda ctx, **kargs: model_filter(
                            _query_or_model( model, attr, ctx.root),
                            kargs, with_count=True, ctx=ctx ),
                        **resolver_kargs),
            **make_filter( ql_inmodel, export=True) )

class namespace_wrapper:
    '''for subnamespacing - putting certain stuff one level deeper.
    name these prefixed with WRAP_TYPE - for easier distinction from others
    or better, add metainfo/description 'wrapper' or simialr
    '''
    @classmethod
    def aresolver( klas, root, info, **kargs):
        r = klas()
        r._parent = root
        return r
    @classmethod
    def Field( klas):
        return graphene.Field( klas, resolver= klas.aresolver)#, description= metainfo_put( wrapper= True))


######## embed_filter_on_tomany_relations
from graphene.types.argument import to_arguments
from graphene_django.fields import DjangoListField #, maybe_queryset
from .base import construct_fields, cleanup_exclude_fields

import inspect
#graphene_django <  2.6: #def list_resolver( resolver, root, info, **args):
#graphene_django >= 2.6: #def list_resolver( django_object_type, resolver, root, info, **args):
#graphene_django >= 2.8: #def list_resolver( django_object_type, resolver, default_manager, root, info, **args
dj_list_args = inspect.signature( getattr( DjangoListField.list_resolver, 'my', 0) or DjangoListField.list_resolver).parameters
#has_django_object_type = 'django_object_type' in dj_list_args
dj_list_root_ix = list( dj_list_args ).index( 'root')
#dj_list_resolver = DjangoListField.list_resolver

class ListResolver( Resolver):
    def __call__( *aa, **kargs):
        me, *bb = aa
        head = bb[ :dj_list_root_ix ]
        rest = bb[ dj_list_root_ix: ]
        me.head_args = head
        return super( ListResolver, me ).__call__( *rest, **kargs)  #XXX this form of super !
    def prep_resolver( me, ctx):
        ctx.head_args = me.head_args
    preparers = Resolver.preparers + [ prep_resolver ]

def _atype( ftype, queryset_wrapper =None):
    t = ftype()
    if t:
        if not queryset_wrapper: queryset_wrapper = lambda x: x
        #ver<2.5 : t is [RelateTo] ; v>=2.5 : t is [RelateTo!]!
        ll = t._type    #may-be-list
        if isinstance( ll, graphene.NonNull): ll = ll.of_type
        oo = ll.of_type #may-be-item
        if isinstance( oo, graphene.NonNull): oo = oo.of_type
        ql_inmodel = _ftypes[ oo._meta.model]
        t.args.update( to_arguments( make_filter( ql_inmodel)))
        #model_filter further from resolved rel
        t.list_resolver = ListResolver( lambda ctx, **kargs: _model_filter(
                            queryset_wrapper(
                                DjangoListField.list_resolver( *ctx.head_args, ctx.root, ctx.info, **kargs)),
                            kargs, parent= ctx.root, ctx=ctx )   #root
                            )
    return t

def embed_filter_on_tomany_relations( ql_model, model_field2query_wrapper ={}):
    cnts = {}
    for k,f in ql_model._meta.fields.items():
        if not is_rel_tomany( f): continue
        # either graphene.Dynamic or ReverseGenericManyToOneDescriptor here
        if isinstance( f, graphene.Dynamic):
            queryset_wrapper = model_field2query_wrapper.get( (ql_model._meta.model,k) )
            f.type = lambda _t=f.type, _qw=queryset_wrapper: _atype( _t, _qw)
        m = f.relmodel
        if m in _types:
            cnts[ k+'_count'     ] = make_count(     m, attr=k ).Field()
            cnts[ k+'_all_count' ] = make_all_count( m, attr=k )
    ql_model._meta.fields.update( cnts)


from django.contrib.contenttypes.fields import ReverseGenericManyToOneDescriptor
def add_generic_relations( model, ql_model, excludes =()):
    for attr in dir(model):
        rel = getattr(model, attr)
        if not isinstance(rel, ReverseGenericManyToOneDescriptor):
            continue
        if attr in excludes: continue
        relmodel = rel.rel.model
        if relmodel not in _types:
            continue
        fql = graphene.Field(
            graphene.List( _types[ relmodel]),
            resolver= lambda root, info, local_attr=attr[:]: getattr(root, local_attr).all()
            )
        fql.relmodel = fql.generic_relation_tomany = relmodel
        ql_model._meta.fields[ attr] = fql


from graphql.type.definition import is_abstract_type
_wrap_types = {}
def add_qmethods( ql_model, **q_methods):
    ql_interfaces = getattr( ql_model._meta, 'interfaces', ())
    if q_methods:
        interfaces = tuple( _wrap_types[ iface] for iface in ql_interfaces if iface in _wrap_types )
        root = graphene.Interface if issubclass( ql_model, graphene.Interface) else graphene.ObjectType
        mname = ql_model._meta.model.__name__
        qwrap = type( WRAP_TYPE+ 'q_'+mname, (namespace_wrapper, root,), dict(
                                q_methods,
                                **(dict( Meta= dict( interfaces= interfaces)) if interfaces else {})
                                )
                )
        _wrap_types[ ql_model] = qwrap
        _q = qwrap.Field()
        q_methods = dict( _q = _q)

    ql_model._meta.fields.update( q_methods)
    for iface in ql_interfaces: #getattr( ql_model._meta, 'interfaces', ()):
        ql_model._meta.fields.update( (k,f)
            for k,f in iface._meta.fields.items()
            if k not in ql_model._meta.fields )


######## make types

def make_polymorphic( model, submodels, extra_fields ={}, POLYMORPHIC_AS_UNION =False):
    mname = model.__name__
    if POLYMORPHIC_AS_UNION:
        base = graphene.Union
        iattrs = dict(
            Meta= dict( types= [ _types[m] for m in submodels ],),
            )
    else:
        base = graphene.Interface
        iattrs = construct_fields( model, registry= oregistry, only_fields=(),
                    exclude_fields= () #[ x.__name__.lower() for x in submodels ]     #django/inheritance
                    )
    ql_model = type( mname, (base,) , dict(
            **iattrs,
            **extra_fields))
    change_frozen_meta( ql_model, model= model, connection=None)
    oregistry.register( ql_model)
    return ql_model

def make_ql_for_model( model, namespace =_query, polymorphic ={}, exclude_fields =(),
                    wraptypename =None, wraprenamer =None, POLYMORPHIC_AS_UNION =False,
                    extra_orderby =(), extra_select_related =(), extra_prefetch_related =(),
                    extra_exclude_fields4filter =(), modelname =None,
                    extra_exclude_fields4filter_func =None,
                    model_filter =None, resolver_kargs ={}):
    if not model_filter: model_filter = _model_filter
    if not modelname: modelname = model.__name__
    model2polybases = defaultdict( list)
    for k, v in polymorphic.items():
        for i in v:
            model2polybases[i].append( k)

    if model in polymorphic:
        ql_model = make_polymorphic( model, polymorphic[ model], POLYMORPHIC_AS_UNION=POLYMORPHIC_AS_UNION)
    else:
        interfaces = []
        if not POLYMORPHIC_AS_UNION:
            interfaces += [ _types[x] for x in model2polybases.get( model, []) ]

        exclude_interface_polymorphic_fields = []
        for i in model2polybases.get( model, []):
            exclude_interface_polymorphic_fields += [ x.__name__.lower() for x in polymorphic[ i]]
            #but they're still visible because of interfaces

            if 0:            #mmh this is just 'id'     #django/inheritance
                exclude_interface_polymorphic_fields += [ i._meta.pk.name ],
            else:
                exclude_interface_polymorphic_fields += [ model._meta.pk.name ]

        ql_model = type( modelname, ( DjangoObjectType,) , dict(
                        Meta= dict( model= model,
                                exclude_fields= cleanup_exclude_fields( model, list(exclude_fields) + exclude_interface_polymorphic_fields),
                                **(dict( interfaces= interfaces) if interfaces else {})
                                ),
                        #**extra_fields,
                        #something = graphene.Field( lambda _m=model: _types[_m], id= graphene.Int(),
                        #    resolver= lambda root,info,_m=model, **kargs: kargs.get('id') and _m.objects.get( id= kargs['id'])
                        #    ),
                        #friends = graphene.List( lambda _m=model: _types[_m], id= graphene.Int(),
                        #    #how to get to self? i.e. self.friends
                        #    resolver= lambda root,info,_m=model, **kargs: kargs.get('id') and _m.objects.h_related_to_or_duplex( _m.objects.get( id= kargs['id']))
                        #    ),
                   ))

        for f in exclude_interface_polymorphic_fields:    #ayee some are still there
            ql_model._meta.fields.pop(f,0)
    for f in exclude_fields: #ayee some are still there
        ql_model._meta.fields.pop(f,0)

    _types[ model ] = ql_model
    #ql_inmodel goes into _ftypes
    if extra_exclude_fields4filter_func:
        extra_exclude_fields4filter += extra_exclude_fields4filter_func( model)
    ql_inmodel = make_inmodel( model, polymorphic, list( exclude_fields) + list( extra_exclude_fields4filter),
                                modelname= modelname,
                                extra_orderby= extra_orderby,
                                extra_select_related= extra_select_related,
                                extra_prefetch_related= extra_prefetch_related,
                                )
    methods = dict(
        all     = make_all( model, model_filter= model_filter, resolver_kargs= resolver_kargs),
        count   = make_count( model, model_filter= model_filter, resolver_kargs= resolver_kargs),
        all_count = make_all_count( model, model_filter= model_filter, resolver_kargs= resolver_kargs),
        )
    if model._meta.pk:
        methods.update( one = make_one( model, ql_model, resolver_kargs= resolver_kargs) )

    if not WRAP_TYPE_ONLY:
        lname = modelname   #XXX? not used any more
        namespace.update( (lname if k == 'one' else lname+'_'+k, v) for k,v in methods.items())
    if WRAP_TYPE:
        ql_wrap = type( WRAP_TYPE + (wraptypename or modelname), (namespace_wrapper, graphene.ObjectType,), dict(
            model = model,
            **methods
            ))
        lname = ql_wrap.__name__.lower()
        if WRAP_TYPE_ONLY: lname = lname[ len(WRAP_TYPE):]
        if wraprenamer: lname = wraprenamer( lname)
        namespace[ lname ] = ql_wrap.Field()
    _query2model[ lname] = model
    return ql_model, ql_inmodel

'''
polymorphics = { base: [ children] , .. }
for model in whatevers:
    make_ql_for_model( model, _query, polymorphics)
'''

#see example.gql XXX

# vim:ts=4:sw=4:expandtab
