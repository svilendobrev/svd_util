import graphene
from graphene_django.fields import DjangoListField, maybe_queryset
import itertools
from svd_util.dicts import dictAttr

names = list( sorted( set( itertools.chain( *[ x.split(':')[0].split() for x in '''
    self fn             : graphql.execution.executors: def execute( self,fn, *a,**ka): ... in all of them
    resolver root info  : DjangoListField.list_resolver( resolver, root, info, **args):
    self next root info : DjangoDebugMiddleware.resolve( self, next, root, info, **args):
    next                : graphql.execution.middleware.make_it_promise( next, *a, **b):
    attname default_value root info :   graphene/types/resolver .attr_resolver(attname, default_value, root, info, **args) ; also .dict_resolver

    type                : Interface/Union.resolve_type

    ctx                 : my wrapper
    me                  : my stuff
    args kargs kwargs arg karg kwarg a ka : just in case
    schema document_ast  executor : maybe.. no. backend.core.execute_and_validate(schema, document_ast, *args, **kwargs):
    '''.strip().split('\n')]))))
#print( names)

if 0:   #way too fiddly to setup and test the DjangoListField on P.children .. faked below
    from django.db import models
    class P( models.Model): pass
    class C( models.Model):
        parent = models.ForeignKey( P, related_name= 'children', on_delete=models.CASCADE)

def getpath( info, pfx):
    return getattr( info, 'path', f'?{pfx}:{info}')
def fielddef( res):
    return dict(
        args = dict( (arg, graphene.Int()) for arg in names),
        resolver = lambda *a,**kargs: RESULTS[ res] , #[
                        #print( 444444444444, getpath( a[1], 111), kargs, ),
                        #][0 ]
        )

from graphene_django import DjangoObjectType
from django.db import models
class somedjObj( models.Model):
    class Meta: abstract=True
    d = models.IntegerField()
class someObj( DjangoObjectType):
    Meta = dict( model = somedjObj)

RESULTS = dictAttr(
    one     =  123 ,
    list    = [456],
    #djlist  = [789],
    djlist0 = [ dict( d=6) ],
    djlist  = [ somedjObj( d=6) ],
    iface = dict(
        type= 259,
        x   = 287,
        b   = 262,
        )
)
def _RESULTS( f):
    rf = RESULTS[f]
    if f == 'djlist': rf = RESULTS[ 'djlist0']
    return rf

class IFace( graphene.Interface):
    x    = graphene.Int()
    type = graphene.Int()

class ofIFace( graphene.ObjectType):
    Meta = dict( interfaces= [ IFace] )
    b = graphene.Int()


class tquery( graphene.ObjectType):
    one     = graphene.Field( graphene.Int, **fielddef( 'one'))
    list    = graphene.List(  graphene.Int, **fielddef( 'list' ))
    djlist  = graphene.List(  someObj, **fielddef('djlist'))

    aiface   = graphene.Field( IFace,   resolver= lambda *a,**ka: ofIFace( **RESULTS.iface))
    aofiface = graphene.Field( ofIFace, resolver= lambda *a,**ka: ofIFace( **RESULTS.iface))

import os
UNFIX = os.environ.get( 'UNFIX')

# XXX HACK fixes: remove named func-arguments to allow them in kargs i.e. arguments of the field
from svd_util.grafql import fixes

if not UNFIX and not os.environ.get( 'UNFIX_DJLIST'):
  if 1: fixes.fix_DjangoListField_list_resolver()
  else:
    def fixed_fake_resolver( *a,**kargs):
        me,resolver,root,info = a
        #print( getpath( info, 222), kargs, ),
        root = dictAttr( djlist= RESULTS.djlist)     #fake it for attr_resolver .. or expect None?
        return maybe_queryset( resolver( root,info, **kargs))
    DjangoListField.list_resolver = fixed_fake_resolver
    #DjangoListField.list_resolver = lambda *a, **kargs: #maybe_queryset( a[1]( *a[2:], **kargs))

else:
    #fake the root for attr_resolver .. or expect None?
    def fakeroot_resolver( *a,**kargs):
        #print( getpath( a[2], 333), kargs, )
        return DjangoListField._list_resolver( a[1], dictAttr( djlist= RESULTS.djlist),a[2], **kargs)
    DjangoListField._list_resolver = DjangoListField.list_resolver
    DjangoListField.list_resolver = fakeroot_resolver

if not UNFIX and not os.environ.get( 'UNFIX_SYNCEXEC'):
 if 1: fixes.fix_SyncExecutor_execute()
 else:
    from graphql.execution.executors.sync import SyncExecutor
    SyncExecutor.execute = lambda *a,**kargs: a[1]( *a[2:], **kargs) #print( 3333333, a[1])

if not UNFIX and not os.environ.get( 'UNFIX_DJMW'):
 if 10: fixes.fix_DjangoDebugMiddleware_resolve()
 #else:
 #   #HACK avoid DjangoDebugMiddleware
 #   from graphene_django import settings
 #   settings.DEFAULTS[ 'MIDDLEWARE' ] = ()

if not UNFIX and not os.environ.get( 'UNFIX_MAKEPROMISE'):
 if 1: fixes.fix_make_it_promise()
 else:
    from graphql.execution import middleware
    middleware.make_it_promise = lambda *a,**b: middleware.Promise.resolve( a[0](*a[1:], **b))

if not UNFIX and not os.environ.get( 'UNFIX_ATTRRES'):
  if 1: fixes.fix_attr_resolver()
  else:
    from graphene.types import resolver
    resolver.attr_resolver = lambda *a,**kargs: getattr( a[2], a[0], a[1])
    resolver.dict_resolver = lambda *a,**kargs: a[2].get( a[0], a[1])
    resolver.default_resolver = resolver.attr_resolver
    #beware of set_default_resolver there

if not UNFIX and not os.environ.get( 'UNFIX_IFACE'):
  if 1: fixes.fix_Interface_resolve_type()
  else:
    ######## HACK fix Interface.resolve_type  ; Union also has one but it does not matter there
    graphene.Interface._resolve_type = graphene.Interface.resolve_type
    del graphene.Interface.resolve_type
    from graphene.types.typemap import TypeMap
    TypeMap._construct_interface= TypeMap.construct_interface
    def construct_interface(self, map, type):
        type.resolve_type = type._resolve_type
        r = self._construct_interface( map,type)
        del type.resolve_type
        return r
    TypeMap.construct_interface= construct_interface

####################

schema = graphene.Schema( query= tquery,
            mutation= tquery,
            auto_camelcase=False,
            )
#print( schema)

from graphene_django.views import GraphQLView

gv = GraphQLView( schema)

def make_query_all():
    return '\n'.join( ['{']+
                [ n+'( '+', '.join( a+':21' for a in names) +')' + ( '{d}' if n=='djlist' else '')
                    for n in 'one list djlist'.split()
                ] + ['}'])

def make_query_1( f,arg):
    return '\n'.join( ['{']+
                [ f + '( '+arg+':13 )' + ( '{d}' if f=='djlist' else '')
                ] + ['}'])

from django.test import TestCase
import unittest.util
unittest.util._MAX_LENGTH=55*1000
#unittest.util._MIN_COMMON_LEN=0

from collections import OrderedDict as odict

class t( TestCase):
    maxDiff = None
    METHOD = 'get'
    def go( me, q):
        return gv.execute_graphql_request(
            request = dictAttr(
                method= me.METHOD,
                ),
            query = q,
            variables = None,
            operation_name =None,
            data = None,
            )

    def test_all_all( me):
        r = me.go( make_query_all() )
        me.assertEqual( r.errors, None)
        me.assertEqual( r.data, odict( (k, _RESULTS(k)) for k in 'one list djlist'.split()))
    if not fixes.v3:
     def test_ifacetype( me):
        r = me.go( '{ aiface { type x } }')
        me.assertEqual( r.errors, None)
        me.assertEqual( r.data, odict( aiface= odict( (k,v) for k,v in RESULTS.iface.items() if k != 'b' )) )
     def test_ofifacetype( me):
        r = me.go( '{ aofiface { type x b } }')
        me.assertEqual( r.errors, None)
        me.assertEqual( r.data, odict( aofiface= odict( RESULTS.iface )) )

import traceback
def fstr(me): return '''{message}
 ql-path: {path}
 orig.error: {orgerr}: {orgmsg}
 stack:
{stack}'''.format( message=me.message, path=me.path,
                orgerr= getattr( me, 'original_error', None) and me.original_error.__class__.__name__,
                orgmsg= getattr( me, 'original_error', '?'),
                    stack = ''.join(traceback.format_tb( getattr( me, 'stack', None) or getattr( me, '__traceback__', None))))
import unittest.mock
from graphql import GraphQLError
mp = GraphQLError.__module__
unittest.mock.patch( mp+'.GraphQLError.__str__', fstr)(t)
unittest.mock.patch( mp+'.GraphQLError.__repr__', fstr)(t)


def tester1( me, f,arg):
    q = make_query_1( f,arg)
    #print( 444444, q)
    r = me.go( q)
    me.assertEqual( r.errors, None)
    me.assertEqual( r.data, { f: _RESULTS(f) } )

for n in names:
    setattr( t, 'test_'+n,    lambda me, n=n: tester1( me, 'one', n))
    setattr( t, 'test_l_'+n,  lambda me, n=n: tester1( me, 'list', n))
    setattr( t, 'test_dl_'+n, lambda me, n=n: tester1( me, 'djlist', n))

if 0:
  class tmut( t):
    METHOD = 'post'
    def go( me, q):
        return super().go( 'mutation ' + q)

# vim:ts=4:sw=4:expandtab
