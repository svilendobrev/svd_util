import graphene
#from django.core import exceptions
from django.db import models
from django.db import transaction
from .base import id2obj, Resolver, error, get_field, dorequire, unrequire
from .get  import _types, construct_fields

#from graphene.types.utils import get_type
def assert_permission( check, msg =None):
    if not check: raise error.PERMISSION_DENIED( msg)

_mutate = {}

if 0:
  class Error( graphene.ObjectType):
    name = graphene.String()
    code = graphene.Int()
    #type: Auth,Perm,Needs,Invalid,... Enum

Noresult = graphene.ID

#def asserter( cond, msg): assert cond, msg

#HACK: store model-type info in it..
#TODO see usage.. automate it somehow
def ID( required, type =None, primary =False ): return graphene.ID( required= required, description= type and 'of:'+type + bool(primary)*':primary' )
def ID_optional( type =None, primary =False ): return ID( required=False, type= type, primary= primary)
def ID_required( type =None, primary =False ): return ID( required= True, type= type, primary= primary)

def make_field( model, field_name, required =None, registry =None):
    f = get_field( model, field_name, registry )
    if required is not None: f = (dorequire if required else unrequire)( f)
    return f

def make_field_auto( model, field_name, required, registry =None):
    modelfield = model._meta.get_field( field_name)
    if modelfield.primary_key:
        return ID( type= model.__name__, required= required, primary= True)
    if modelfield.is_relation and (modelfield.many_to_one or modelfield.one_to_one):
        if required is None: required = not modelfield.null
        related_model_name = modelfield.related_model
        if not isinstance( related_model_name, str): related_model_name = related_model_name.__name__
        return ID( type= related_model_name, required= required)
    assert not modelfield.is_relation, 'relation to-many is DIY: '+field_name # XXX
    return make_field( model, field_name, required, registry)

@transaction.atomic
def obj_update( obj, values, force_update =False):
    #TODO recursive nesting down?
    for k,v in values.items():
        if obj._meta.get_field( k).many_to_many:
            #if attr in info.relations and info.relations[attr].to_many:
            getattr( obj, k).set( v)
        else:
            setattr( obj, k, v)
    if values or force_update:
        obj.save()
    return obj

def model_update( model, pk, values, **ka):
    return obj_update( id2obj( model, pk), values, **ka)

@transaction.atomic
def model_create( model, values):
    #TODO recursive nesting down?
    many_to_many = dict( (k,v) for k,v in values.items() if model._meta.get_field( k).many_to_many)
    values = dict( (k,v) for k,v in values.items() if k not in many_to_many)

    obj = model.objects.create( **values)
    for k,v in many_to_many.items():
        getattr( obj, k ).set( v)
    return obj

######
User = None # from django.contrib import auth .get_user_model()

ql_arg_auth_user = dict(
    auth_user = ID_required(),  #XXX actualy comes from auth!
    )
def ql_get_auth_user( ctx, kargs):
    return id2obj( User, kargs.pop('auth_user'))

AUTH_FROM_ELSEWHERE = 10
if AUTH_FROM_ELSEWHERE:
    arg_auth_user = {}
    get_auth_user = ...
else:
    arg_auth_user = ql_arg_auth_user
    get_auth_user = ql_get_auth_user


AUTH = 0

def deco_resolver( f=None, *, auth_user =None,
        id2obj =None,   #None; False: id2int; True: id2obj of field-return-type; str: fieldname-of-pk, like True; model: id2obj of the model
        **kargs
        ):
    if auth_user is None: auth_user = AUTH
    assert f is None or callable(f), f
    def decor( func):
        func.deco_resolver = True
        return Resolver( func, auth_user=auth_user, id2obj=id2obj, **kargs)
    if f is not None: return decor(f)
    return decor

def mufield( return_type, args, mutator, auth_user =None, id2obj =None, is_list =False, **kargs):
    if auth_user is None: auth_user = AUTH
    qlmodel = _types[ return_type] if return_type and isinstance( return_type, type) and issubclass( return_type, models.Model) else return_type
    if is_list:
        qlmodel = graphene.List( qlmodel)
    if not hasattr( mutator, 'deco_resolver'):
        mutator = deco_resolver( mutator, auth_user=auth_user, id2obj=id2obj, **kargs)
    return graphene.Field( qlmodel, args= dict(
                        **(arg_auth_user if auth_user else {}), #err if overlap with args
                        **args,
                        ),
                    resolver = mutator
                    )

def mufield_deco( model, args ={}, **kargs):
    def decor( func):
        _mutate[ func.__name__ ] = mufield( model, args, func, **kargs)
        return func
    return decor

def make_args_auto( model, args, **ka):
    'args = { fieldname: bool_is_required or the-actual-field }'
    return dict( (k,
            vreq if not isinstance( vreq, bool) else make_field_auto( model, k, vreq)
            ) for k,vreq in args.items())
if 0:
    example = make_field_auto( models.Role, args= dict(
        user = True,
        type = False,
        somespecial  = graphene.List( graphene.String, ...),
        renamed_type = make_field( models.Role, 'type', True),  #renaming
        ),)

def mufield_deco_auto( model, args, **ka):
    return mufield_deco( model, args= make_args_auto( model, args), **ka)

#######
if 0:
    @mufield_deco_auto( models.Role, args= dict(
                    user    = True, #ID_required( 'User'),
                    holder  = True, #ID_required( 'Holder'),
                    asset   = False, #ID_optional( 'Asset'),
                    type    = True, #dorequire( get_field( models.Role, 'type'))
                ),  id2obj=True)
    def role_allow( ctx, user, holder, type, asset =None):
        if 0:
            assert_permission( CAN_MANAGE_ROLES( ctx.auth_user, holder))
        return models.Role.allow( user=user, holder=holder, type=type, asset=asset)

    @mufield_deco( Noresult, args= dict(
                    user    = ID_optional( 'User'),
                    holder  = ID_optional( 'Holder'),
                    asset   = ID_optional( 'Asset'),
                    type    = unrequire( get_field( models.Role, 'type'))
                ),  id2obj= models.Role)
    def role_disallow( ctx, user =None, holder =None, type =None, asset =None):
        assert_correct_input( user or holder or asset, 'cannot disallow everything')
        if 0:
            assert_permission( CAN_MANAGE_ROLES( ctx.auth_user, holder))
        #XXX #assert_correct_input( r.type != models.Role._types.OWNER, 'Owner role cannot be deleted. delete the company/holder of it' )
        models.Role.disallow( user=user, holder=holder, type=type, asset=asset)
        return #no result/error


    @mufield_deco( Noresult, auth_user= True)
    def user_self_disable( ctx):
        user = ctx.auth_user
        user.is_active = False
        user.save()
        #users.logout( request)
        return #no result/error

    @mufield_deco( models.User, auth_user= True, args= dict(
                    holder = ID_required(),
                    ))
    def user_set_default_holder( ctx, holder):
        user = ctx.auth_user
        holder = id2obj( models.Holder, holder)
        assert_permission( models.Role.is_allowed( user, holder))
        user.default_holder = holder
        user.save()
        return user

    @mufield_deco( models.Company, args= dict(
                    id   = ID_required(),
                    data = dorequire( get_field( models.Company, 'data')),
                ),  id2obj=True, )
    def company_edit( ctx, id, **kargs):
        return obj_update( id, kargs)

    def make_asset_new( model):
        return model.__name__.lower()+'_add', mufield(
                model, args= dict(
                    holder  = ID_required(),
                    data    = dorequire( get_field( model, 'data')),
                ),  id2obj=True,
                mutator= lambda ctx,**kargs: model.objects.create(**kargs)
                )

    def make_asset_edit( model):
        return model.__name__.lower()+'_edit', mufield(
                model, args= dict(
                    id      = ID_required(),
                    holder  = ID_optional(),
                    data    = unrequire( get_field( model, 'data')),
                ),  id2obj=True,
                mutator= lambda ctx,id,**kargs: obj_update( id, kargs)
                )

    def make_model_del( model):
        def model_del( ctx, id):
            o = model.objects.filter( pk= model._meta.pk.to_python( id) )
            if 0:
                o = o.first()
                if o:
                    if issubclass( model, models.Asset):
                        assert_permission( CAN_MANAGE_ASSETS( ctx.auth_user, holder= o.holder))
                    ...
            o.delete()
            return #no result/error
        return model.__name__.lower()+'_del', mufield(
                Noresult, args= dict(
                    id  = ID_required(),
                ),  #id2obj=False,
                mutator= model_del
                )

    _mutate.update( make_asset_new(  m) for m in all_assets )
    _mutate.update( make_asset_edit( m) for m in all_assets )
    _mutate.update( make_model_del(  m) for m in all_assets )
    _mutate.update( make_model_del(  m) for m in [ ... ])

# vim:ts=4:sw=4:expandtab
