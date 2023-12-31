import graphene
from graphene_django.registry import Registry, get_global_registry
import copy
from svd_util.dicts import dictAttr

from django.core.exceptions import ObjectDoesNotExist

class _Error:
    class QLError( RuntimeError): pass
    types = dict( (k,k) for k in '''
        AUTH_NEEDED
        PERMISSION_DENIED
        WRONG_INPUT
        DOES_NOT_EXIST
        '''.split())
    exc2type = {
        ObjectDoesNotExist: 'DOES_NOT_EXIST',
        #models.WrongInputError: 'WRONG_INPUT',     #validation-err
        #...
        }

    def _err( me, type, msg, **ka):
        assert type in me.types, type
        r = me.QLError( msg or me.types[type] )
        r.type = type
        r.moreargs = ka
        return r

    @classmethod
    def convert_exc( me, exc, errdata=None):
        for klas,errtyp in me.exc2type.items():
            if isinstance( exc, klas):
                if callable( errtyp):
                    r = errtyp( exc, errdata or {})       #XXX
                    return r
                return errtyp

    def __getattr__( me, k):
        if k in me.types:
            return lambda msg=None, **ka: me._err( k, msg, **ka)
        return super().__getattr__( k)
error = _Error()

from django.conf import settings
import traceback, itertools

FORMAT_ERROR_NO_TRACEBACK = 0
from graphene_django.views import GraphQLView
_format_error = GraphQLView.format_error
@staticmethod
def format_error( error_):
    r = _format_error( error_)
    typ = None
    original_error = getattr( error_, 'original_error', None)
    if original_error:
        if isinstance( original_error, _Error.QLError):
            typ = original_error.type
            if original_error.moreargs:
                assert not (set(original_error.moreargs ) & set( r)), (r,original_error)
                r.update( original_error.moreargs)
        else:
            typ = _Error.convert_exc( original_error, r)
        if typ:
            r['type'] = typ
            assert typ in error.types, typ
        else:
            #usualy in tests, importing from . instead of from /root/path/...
            assert type(original_error).__name__ != 'QLError', (original_error, id( type(original_error)), id( QLError) )
            r['message'] = original_error.__class__.__name__ + ': ' + r['message']
    tb_v3 = getattr( error_, '__traceback__', None)
    tb_v2 = getattr( error_, 'stack', None)
    stack = settings.DEBUG and (tb_v3 or tb_v2)  #XXX beware, test-runner kills settings.DEBUG
    if stack:
        r['traceback'] = list(itertools.chain( *[a.strip().split('\n') for a in traceback.format_tb( stack)] )) #''.join(traceback.format_tb(stack))
        if tb_v3 and not typ:
            #print('not one of _Error.. show it')
            traceback.print_exception( type(original_error), original_error, tb_v3)
            if FORMAT_ERROR_NO_TRACEBACK: r.pop('traceback')
    return r
GraphQLView.format_error = format_error



def get_request_from_info( info): return info.context
def get_auth_user_from_info( info): return info.context.user
def get_request(   ctx): return ctx.info.context
def get_auth_user( ctx): return ctx.info.context.user

#TODO
# +  qlField(..) arguments clash with some funcs on the execute/resolve way.. see testargs.py, and HACKs below
# -- Resolver func: ctx, kargs and not ctx,**kargs.. no need

import graphql
Undefined = getattr( graphql, 'Undefined', None)

class Resolver:
    def __init__( me, func, log =True,
            auth_user =False,   #= whether required ; stored in ctx regardless
            id2obj =None,   #None; False: id2int; True: id2obj of field-return-type; str: fieldname-of-pk, like True; model: id2obj of the model
            exclude =(),
            **options):
        me.func = func
        me.options = dictAttr( log=log, auth_user=auth_user, id2obj=id2obj, exclude=exclude, **options)
    def __str__( me):
        return f'{me.__class__.__name__}: {me.func.__name__} {me.options}'

    def __call__( *aa, **kargs):
        ''' resolve-a-field call context: root, info, kargs
        root : the object/namespace containing this resolving-field; None means the root query/mutation
        info.context    : dj-wsgi-request
        info.field_name : name of this field
        info.return_type: gql-type returned by this field
        info.parent_type: gql-type of the object/namespace containing this field, use parent_type.graphene_type
        info.path   :   path from root including field_name above
        '''
        me, root, info = aa
        try:
            info = dictAttr( info._asdict())
        except AttributeError:
            info = dictAttr( (k,getattr(info,k)) for k in info.__class__.__slots__)
        if hasattr( info.path, 'as_list'): info.path = info.path.as_list()
        ctx = dictAttr( root=root, info=info, args=kargs)
        for ctxprep in me.preparers:
            ctxprep( me, ctx)
        #print( 775553, ctx.get('holder_on_behalf'))
        return me.func( ctx, **kargs)

    def log( me, ctx):
        if me.options.log:
            log( **ctx)

    User = None
    def auth_user( me, ctx):
        ctx.auth_user = get_auth_user( ctx) #, ctx.args)
        #print( 17777, ctx.auth_user)
        if me.options.auth_user:
            if not isinstance( ctx.auth_user, me.User):
                raise error.AUTH_NEEDED()   #XXX differ between non-auth and auth-but-inactive-user??

    def id2idobj( me, ctx):
        if me.options.id2obj is not None:
            id2idobj( ctx.root or ctx.info.parent_type.graphene_type, ctx.info.field_name, ctx.args, toobj= me.options.id2obj, exclude= me.options.exclude)

    preparers = [ log, auth_user, id2idobj ]

log_disabled = False
def log( root, info, args, **kargs):
    if not log_disabled:
        print( ' >', '.'.join( str(x) for x in info.path if x), args, kargs or '')

def id2obj( model, id):
    if id is None: return
    pk = model._meta.pk.to_python( id)
    #try:
    return model.objects.get( pk= pk)
    #except model.DoesNotExist: return

def id2idobj( qltype, field_name, kargs, toobj =False, exclude= ()):
    ''' turn all ids (of kargs=input) into pk-type or django-object
    qltype: roottype if field_name, else actual inputType matching toobj
    toobj: True/False/the-pk-fieldname/the-obj-model
    +a: fetch the objects here
     b: all them funcs to be able to work with both x=model and x=id-of-model (x_id=..)
    '''
    if field_name:
        qlfield = qltype._meta.fields[ field_name ]     #graphene
        qlfargs = qlfield.args
    else:
        qlfield = qltype
        qlfargs = qlfield._meta.fields
    #print( qltype._meta.fields[ field_name ]     #graphene
    model = toobj if toobj and toobj is not True and not isinstance(toobj,str) else qlfield.type._meta.model
    dj_fmap = model._meta._forward_fields_map    #or fields_map ?
    for k,v in kargs.items():
        if exclude and k in exclude: continue
        argtype = qlfargs[ k].type
        if isinstance( argtype, graphene.NonNull):
            argtype = argtype.of_type
        if argtype is not graphene.ID: continue

        if (k == 'id' or k == toobj) and k not in dj_fmap:
            dj_field = model._meta.pk
        else:
            dj_field = dj_fmap[k]
        if toobj:
            #try:
            v = id2obj( model if dj_field.primary_key else dj_field.related_model, v)
            #except exceptions.ObjectDoesNotExist:  XXX ?
        else:
            v = dj_field.to_python( v)
        kargs[ k] = v
    return kargs

################

#CMP_IS_SEPARATE_FIELD = True


def is_required( f):    #XXX f = fld.type for Field()s
    return isinstance( f, graphene.NonNull) or getattr( f, 'kwargs', {}).get( 'required', None)

def unrequire( f):
    if isinstance( f, graphene.NonNull):
        f = f._of_type()
    elif getattr( f, 'kwargs', {}).get( 'required', None):
        f = copy.copy( f)
        f.kwargs = f.kwargs.copy()
        f.kwargs.pop( 'required')
    return f

def dorequire( f):
    if isinstance( f, graphene.NonNull): return f
    #XXX ?field-to-obj : .type -> NonNull(.type)
    if not getattr( f, 'kwargs', {}).get( 'required', None):
        f = copy.copy( f)
        f.kwargs = f.kwargs.copy()
        f.kwargs[ 'required'] = True
    return f

def _aregister( me, cls):
    if not getattr( cls._meta, 'skip_registry', False):     #why skip would be needed?
        me._registry[ cls._meta.model] = cls
Registry.register = _aregister   #so unions/interfaces can also go there

class AnyRegistry( Registry):
    def __init__( me):
        super().__init__()
        me.org = get_global_registry()
    def get_converted_field( me, field):
        'if non-link, use org field, and maybe make_comparer of it'
        r = super().get_converted_field( field)
        if not r:
            orgfield = me.org.get_converted_field( field)
            if orgfield and not isinstance( orgfield, graphene.Dynamic):
                r = orgfield
                #if not CMP_IS_SEPARATE_FIELD: #turn scalars into comparers
                #    r = make_comparer( orgfield)#, field)

            if r is orgfield:
                r = unrequire(r)
                if r is not orgfield:
                    me.register_converted_field( field, r)
        return r

inregistry = AnyRegistry()
oregistry  = get_global_registry()
def _get_field( modelfield, registry =None):
    return (registry or oregistry).get_converted_field( modelfield)
#    return converter.convert_django_field_with_choices( modelfield, registry or oregistry)     #XXX WHY there was intent/need to replace the above with this? somewhen in apr.2021, never commited
def get_field( model, field_name, registry =None):
    return _get_field( model._meta.get_field( field_name), registry )

def change_frozen_meta( objtype, **ka):
    _meta = objtype._meta
    m = _meta.__class__( objtype)   #frozen.. WTF
    m.__dict__.update( ka)
    for k in dir( _meta):
        if k.startswith( '__') or k == '_frozen': continue
        v = getattr( _meta, k)
        if callable( v): continue
        setattr( m, k, v)
    m.freeze()
    objtype._meta = m


############
#if 'sorted_by_name': #yank_fields_from_attrs is already imported everywhere.. too late replacing. hence..
import collections
from graphene.types import utils
def _sorter(kv):
    n = getattr( kv[1],'name','') or kv[0]
    #if n.endswith('s'): n=n[:-1]+'_s'                  #-> deal, deals, dealitem, dealitems
    #elif n.endswith('s_count'): n=n[:-7]+'_s_count'    #-> deal, deals, deals_count, dealitem, dealitems, dealitems_count
    return (n != 'id' and not n.startswith('id_')),n.startswith('__') or n.isupper(), n
def reOrderedDict( kvs):
    return collections.OrderedDict( sorted( kvs, key= _sorter))
utils.OrderedDict = reOrderedDict

############

def allow_GenericRelation():
    # -a) get_model_fields -> for field in model._meta.get_fields() whole .. pulls GenericForeignKey too
    # +b) get_reverse_field -> only add GenericRelation
    from django.contrib.contenttypes.fields import GenericRelation
    from graphene_django import utils
    def myget_reverse_fields( model, local_field_names):
        r = list( _get_reverse_fields( model, local_field_names))
        r += [ ( field.name, field) for field in model._meta.get_fields() if isinstance( field, GenericRelation) ]
        return r
    if utils.get_reverse_fields is myget_reverse_fields: return
    _get_reverse_fields = utils.get_reverse_fields
    utils.get_reverse_fields = myget_reverse_fields
    from graphene_django import converter
    from django.db import models
    func = converter.convert_django_field.registry[ models.ManyToOneRel ]
    converter.convert_django_field.register( GenericRelation, func)

############

def metainfo_put( **metas):
    #r: ..help.. ;_meta_ m1 m2:v ...
    descr = str( metas.pop( 'help', '' ))
    metadescr = ' '.join( k if v is True else k+f':{v}'
                            for k,v in sorted( metas.items())) # dont if v is not None)
    if metadescr: metadescr = ';_meta_ '+metadescr
    return ' '.join( f for f in [descr, metadescr] if f)

def metainfo_get( descr):
    mm = (descr or '').split( ';_meta_ ')
    if len(mm) == 1: return dict( help= descr)
    return dict( help= mm[0].strip(),
                **dict( kv.split(':') if ':' in kv else (kv,True)
                        for kv in mm[1].split()))


def convert_field_to_string_with_meta( field, registry=None):
    description = field.help_text or ''
    metas = {}
    if isinstance( field, models.FileField ): metas.update( url= True)
    if isinstance( field, models.ImageField): metas.update( image= True)
    description = metainfo_put( help= description,
        size= getattr( field, 'maxsize', field.max_length),
        model= field.__class__.__name__,
        **metas
        )   #this is for genjsui to work
    return graphene.String( description= description, required= not field.null)    #these go into .args/.kwargs

from graphene_django import converter
from django.db import models
textconv = converter.convert_django_field.registry[ models.CharField]
for k in converter.convert_django_field.registry.keys():
    f = converter.convert_django_field.registry[ k]
    if f is textconv:
        converter.convert_django_field.register( k, convert_field_to_string_with_meta)

if 0:  #is this still needed??
 try: models.JSONField
 except AttributeError: pass
 else:
    from django.contrib.postgres.fields import JSONField as pgJSONField
    converter.convert_django_field.register( models.JSONField, converter.convert_django_field.registry[ pgJSONField ])

import inspect
_convert_django_field_with_choices = converter.convert_django_field_with_choices
#cce4convert_django_field_with_choices = 'convert_choices_to_enum' in inspect.signature( _convert_django_field_with_choices).parameters
def convert_django_field_with_choices__modelkind(field, *a,**ka):
    #choices = getattr(field, "choices", None)
    #if choices and cce4convert_django_field_with_choices:
    #    assert not ka.get( 'convert_choices_to_enum'), field
    #    ka.setdefault( 'convert_choices_to_enum', False)
    r = _convert_django_field_with_choices( field, *a,**ka)
    kind = getattr( field, 'kind', None)
    if kind:
        mm = metainfo_get( r.kwargs.get( 'description') or '')
        if 'kind' in mm:
            assert kind == mm['kind'], (mm,kind,field)
        mm.update( kind= kind)
        r.kwargs['description'] = metainfo_put( **mm)
    return r
converter.convert_django_field_with_choices = convert_django_field_with_choices__modelkind
from graphene_django import types
types.convert_django_field_with_choices = convert_django_field_with_choices__modelkind

def graphene_enum( name, values):
    if isinstance( values, str): values = values.split()
    return graphene.Enum( name, [(k,k) for k in values ])

############

from . import fixes
fixes.fix_all_execute_resolve()

from graphene_django.types import construct_fields as _construct_fields, get_model_fields
def cleanup_exclude_fields( model, exclude_fields): #needed for >=2.8
    _model_fields = get_model_fields( model)
    model_field_names = set(field[0] for field in _model_fields)
    if exclude_fields: exclude_fields = [ x for x in exclude_fields if x in model_field_names]
    return exclude_fields

import inspect
cce4construct_fields = 'convert_choices_to_enum' in inspect.signature( _construct_fields).parameters
def construct_fields( model, registry, only_fields, exclude_fields):
    extra_args = {}
    if cce4construct_fields:
        extra_args = dict( convert_choices_to_enum=True)
        #and for maybe diferent version:
        exclude_fields = cleanup_exclude_fields( model, exclude_fields )
    #v 2.8+: only_fields = () -> no fields :/
    return _construct_fields( model, registry, only_fields or None, exclude_fields, **extra_args)

# vim:ts=4:sw=4:expandtab
