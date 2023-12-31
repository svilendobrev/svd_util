import graphene
from graphene_django import settings
settings.DEFAULTS[ 'MIDDLEWARE' ] = () #.. avoid whole



from svd_util.grafql import get, mut
from .models import Role, User, WrongInputError

from svd_util.grafql import base  #    #from . = shizo!
base._Error.exc2type[ WrongInputError] = 'WRONG_INPUT'

for m in [ Role] + (User not in get._types )*[ User ]:
    get.make_ql_for_model( m, get._query, )

from svd_util.grafql.tapql import test_mut #add mutations

class qlQuery( graphene.ObjectType):
    #if PROBA123: locals().update( _qq)
    locals().update( get._query)

class qlMutate( graphene.ObjectType):
    locals().update( mut._mutate)

schema = graphene.Schema(
            query= qlQuery,
            mutation= qlMutate,
            auto_camelcase= False,
            )

from graphene_django.views import GraphQLView
from django.conf.urls import url, include

urlpatterns = [
        url( '^graphql', GraphQLView.as_view( graphiql=True, schema= schema)),# middleware=qlshema.middleware)),
        ]

# vim:ts=4:sw=4:expandtab
