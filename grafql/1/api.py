'''
think of it as schema-defined rpc, where each field is a function on server (by default with no arguments)

requirements.txt:
graphene-django >= 2.1rc1 # graphql
#graphene-django-extras     # ..?
# - Allows to define DjangoRestFramework serializers based Mutations.

vim: https://github.com/jparise/vim-graphql  and move it into ~/.vim/pack/xany/start/

quirks:
- Null is null/None ?
+ non-registered models are ignored from other model's fields
+ auto_camelcase off: schema = graphene.Schema( query= qlQuery, auto_camelcase=False,)
+ debug: add to qlQuery: debug = graphene.Field( DjangoDebug, name='__debug')
+ recursive model: Xmodel contains xx= Field/List( lambda: Xmodel)
+ resolving attr y inside x: x is already resolved - the "root" arg
+ polymorphism ? Interface or Union
    - Union cannot have any fields itself
    + Interface is ok, but has resolve_type conflicting with a field named "type" : below construct_interface fix
+ filtering... no builtin, relay does not count
    -- see https://www.graph.cool/docs/reference/graphql-api/query-api-nia9nushae/
    + expr-language translated into orm hierarchical filters+lookups,
    + AND/OR/NOT
    + orderby, pagination

docs:
 graphql: https://graphql.org/learn/queries/
 relay: https://facebook.github.io/relay/docs/en/thinking-in-relay.html
'''

#TODO
# - query external $arguments sorting...?
#XXX wget ../graphql -> 400 ???

import graphene

from . import get, mut

if 1:
    from graphene_django import settings
    settings.DEFAULTS[ 'MIDDLEWARE' ] = () #.. avoid whole
    DjangoDebug = 0
else:
    from graphene_django.debug import DjangoDebug

PROBA123 = 0
if PROBA123:
    from the.models import SomeModel
    from svd_util.dicts import dictAttr
    from graphene_django import DjangoObjectType

    class X( DjangoObjectType):
        Meta = dict( model = SomeModel)

    class Y( graphene.ObjectType):
        id= graphene.ID( required=True)
        b = graphene.String( required=True)
        c = graphene.String()

    class Z( graphene.ObjectType):
        all = graphene.List( X,
            resolver = lambda *a,**ka: SomeModel.objects.all())

    _qq = dict(
            y = graphene.Field( Y, id= graphene.ID(),
                resolver = lambda *a,**ka: dictAttr( a=3, b= ka.get('id', 'fdf'))),
            x = graphene.Field( X, id= graphene.ID(),
                resolver = lambda *a,**ka: SomeModel.objects.get( id= int(ka['id']))),
            all = graphene.List( X,
                resolver = lambda *a,**ka: SomeModel.objects.all()),
            z = graphene.Field( Z,
                resolver = lambda *a,**ka: Z()),
            )

class qlQuery( graphene.ObjectType):
    if PROBA123: locals().update( _qq)
    locals().update( get._query)
    #..
    if DjangoDebug: debug = graphene.Field( DjangoDebug, name='__debug')

class qlMutate( graphene.ObjectType):
    locals().update( mut._mutate)
    #..
    if DjangoDebug: debug = graphene.Field( DjangoDebug, name='__debug')

schema = graphene.Schema(
            query= qlQuery,
            mutation= qlMutate,
            auto_camelcase= False,
            )
#print( schema)
#see example.gql XXX

# vim:ts=4:sw=4:expandtab
