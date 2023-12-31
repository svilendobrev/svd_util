from django.test import TestCase

from django.db.models import Q
from svd_util.wither import wither

def drf_dt2str( dt):
    from rest_framework import fields
    return fields.DateTimeField().to_representation( dt)
from svd_util.django.models import DUMP
from svd_util.dicts import dictAttr
import itertools
import datetime


from svd_util.grafql import base  #    #from . = shizo!
from svd_util.grafql.filter import _cmpsfx

def objs( klas):    #any query that is not count or exist or get, must use this and not directly klas.objects...
    return klas.objects.order_by( 'id')

from rest_framework.test import APIClient as _APIClient
def APIClient( **ka):
    return _APIClient( HTTP_USER_AGENT='testdrf')

from enum import Enum
class Status( Enum): (
     OK,
     FAIL,
     UNAUTHORIZED,

     PERMISSION_DENIED,
     NOT_FOUND,
     METHOD_NOT_ALLOWED,

     PRECONDITION_FAILED,
     EXPECTATION_FAILED,
     FAILED_DEPENDENCY,

     BAD_GATEWAY
     ) = range( 10)

class tCommon:
    maxDiff= None

    status_codes= {
        Status.OK:                  [ 200, 201, 204 ], #maybe regex ?
        Status.FAIL:                [ 400 ],
        Status.UNAUTHORIZED:        [ 401 ],    #beware: orig.SessionAith has no www-auth header and ApiView.handle_exception turns 401 into 403
        Status.PERMISSION_DENIED:   [ 403 ],
        Status.NOT_FOUND:           [ 404 ],
        Status.METHOD_NOT_ALLOWED:  [ 405 ],
        Status.PRECONDITION_FAILED: [ 412 ],
        Status.EXPECTATION_FAILED:  [ 417 ],
        Status.FAILED_DEPENDENCY:   [ 424 ],
        Status.BAD_GATEWAY:         [ 502 ],
        }
    def ass_resp_status( me, response, status= Status.OK, message =None):
        me.assertIn( response.status_code, me.status_codes[ status],
            ': '.join( str(x) for x in [ status, message, getattr( response, 'data', ''),
                            response.get('Content-Type') and getattr( response, 'json', lambda:'')() or '']
                            if x)
            )
        return response
    def ass_resp_content_json( me, response,):
        me.assertEqual( response['content-type'], 'application/json', response)
    def ass_resp_OK_json( me, response):
        me.ass_resp_status( response, Status.OK)
        me.ass_resp_content_json( response)

    def setUp( me):
        super().setUp()
        me.c = APIClient()

#TODO:
# get
# + one/all/count/all_count
# + flat/nested
# + simple/polymorphic
# filter on all
# + orderby
# + distinct
# + filter flat/nested
# + filter / AND / OR / NOT
# + first/last/skip/page/perpage + errors
# - select_related
# - prefetch_related

#language:
# - field sorting - it is not random

# filter syntax config
# + x
# + x__cmp
#   + generic: eq, in : id text date
#   + specific: gt/lt/etc
#     + text: contains startswith regex ,..
#     + ignorecase as modifier
#       - ignorecase as non-modifier: icontains ..
#     + date: gt/lt
#       - modifiers - year
#   + op__expr
# - relations have filter   e.g. user.roles(..)
# - plural-calc-methods have filter e.g. user.my_holders(..)

# get:
#get_deal_diff_to_initial_snapshot
#get_users_seeing_asset
# mut:
#?? model_create
#user_self_disable
#user_get_or_create_personal_holder
#deal_add/deal_edit/deal_copy - items?
#deal_edit/state_changes ???????? same as deal_set_state_at_current_holder_side


from svd_util.attr import get_attrib
def odict( *a,**ka):
    r = dict( *a,**ka)
    if 'id' in r: r['id'] = str( r['id'])
    return r
def odict_obj( o, *fields):
    return odict( (k,get_attrib(o,k) ) for k in fields)
def q_as_odicts( q, *fields):
    return [ odict_obj( u,*fields) for u in q ]
def qdict_as_odicts( exp, *fields):
    return dict( (k, q_as_odicts( q, *fields)) for k,q in exp.items())

class qstr( str): pass
def qlarg(x):
    if not isinstance(x,str): return str(x)
    if isinstance(x,qstr): return str(x)
    return '"'+x+'"'
def items2qlargs( items):
    if isinstance( items, dict): items = items.items()
    return ', '.join( k+':'+qlarg(v) for k,v in sorted(items) )


import unittest.mock
def shut_up( f, do_base= False):
    f = unittest.mock.patch( 'graphql.execution.executor.logger.disabled', True)(f)
    f = unittest.mock.patch( 'graphql.execution.utils.logger.disabled', True)(f)
    if do_base:
        f = unittest.mock.patch.object( base, 'log_disabled', True)(f)
    return f

class QLFuncs:
    def posts_qry( me, qry, filter ='', quiet =False):
        with unittest.mock.patch( 'graphql.execution.executor.logger.disabled', True) if quiet else wither:
          with unittest.mock.patch( 'graphql.execution.utils.logger.disabled', True) if quiet else wither:
            #with unittest.mock.patch.object( base, 'log_disabled', True) if quiet else wither:
                query = dict( query= qry % dict(
                    filter= filter,
                    #data= data,
                    ))
                return me.c.post( '/graphql/', query)

    def posts_qry_ass_exp( me, qry, exp, filter ='', errors =None, quiet =False):
        quiet = errors or quiet
        if isinstance( qry, str):
            resp = me.posts_qry( qry, filter, quiet =quiet)
        else:
            resp = qry
        me.ass_resp_OK_json(resp)
        if callable( exp): exp = exp()
        data = resp.json().get( 'data')  #all ints->text?
        with subTest( 'data'):
            me.assertEqual( exp, data)
        r_errors = resp.json().get('errors')
        if errors and r_errors:
            r_errors = [ dict( (k,v) for k,v in e.items() if k in errors[0])
                            for e in r_errors ]
        with subTest( 'errors'):
            me.assertEqual( errors, r_errors, r_errors and '\n>'.join( ['']+list( r_errors[0].get('traceback', ()))))   #XXX test-runner kills settings.DEBUG
        return resp

if 0:
    class polymorphic( QLFuncs, tCommon, TestCase):
        CREATE_COUNTS = {
            m.Holder: 1,
            m.Truck:  1,
            }
        NAMED_ASSETS= True

        def test_concrete( me):
            qry = '''{ truck {
                tr_all_items:            all { id data }
                tr_count:                count
                tr_allcount_items:       all_count { data { id data }}
                tr_allcount_items_count: all_count { data { id  data } count }
            }}'''

            q = q_as_odicts( objs( m.Truck).all(), 'id', 'data')
            exp = dict( truck= dict(
                tr_all_items= q,
                tr_count= len(q),
                tr_allcount_items= dict( data= q),
                tr_allcount_items_count = dict( count= len( q), data= q),
            ))
            me.posts_qry_ass_exp( qry, exp)

        def test_polymorphic( me):
            a = m.any.Asset
            t = me.truck1h1
            me.assertEqual( m.Truck.objects.count(), 1)
            me.assertEqual( m.AnyAsset.objects.count(), 4)
            qry = '''{ asset {
                count
                all {
                    __typename id holder { id }
                    ... on Truck { data }
                    ... on AnyAsset { atype }
                }
                t1: one( id: %(tid)s ) {
                    __typename id
                    ... on Truck { data }
                    ... on AnyAsset { atype }
                }
                a1: one( id: %(aid)s ) {
                    __typename id
                    ... on Truck { data }
                    ... on AnyAsset { atype }
                }
            }}''' % dict( tid= t.id, aid= a.id)

            assets = list( objs(m.Asset))
            exp = dict( asset= dict(
                    count= len(assets),
                    all= [ odict(
                            __typename= a.__class__.__name__,
                            holder= dict( id= f'{a.holder_id}'),
                            id = a.id,
                            **( dict( atype=a.atype) if isinstance( a, m.AnyAsset) else dict( data= a.data)))
                        for a in assets ],
                    t1= odict( id = t.id, __typename= t.__class__.__name__,
                            data= t.data),
                    a1= odict( id = a.id, __typename= a.__class__.__name__,
                            atype= a.atype),
                ))
            me.posts_qry_ass_exp( qry, exp)


    class get( QLFuncs, tCommon, TestCase):
        CREATE_COUNTS = {
            m.Holder: 2,
        }

        def _get_roles( me, u, incl_holder =''):
            if isinstance( incl_holder, str): incl_holder = incl_holder.split()
            return [ odict( id = r.id, type= r.type,
                        **( dict( holder= odict_obj( r.holder, *incl_holder)) if incl_holder else {})
                        )
                    for r in objs( m.Role).filter( user= u) ]

        def test_one( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h2, 'MEMBER')

            qry = '''{ user {
                flat: one( id: %(uid)s)
                    { id email }
                nest: one( id: %(uid)s) {
                    id
                    roles
                        { id type holder { id } }
                    }
            }}'''

            u = me.u1
            me.posts_qry_ass_exp( qry % dict( uid= u.id), exp= dict( user= dict(
                flat= odict( id= u.id, email= u.email),
                nest= odict( id= u.id, roles= me._get_roles( u, incl_holder= 'id')),
                )))
            u= me.u2
            me.posts_qry_ass_exp( qry % dict( uid= u.id), exp= dict( user= dict(
                flat= odict( id= u.id, email= u.email),
                nest= odict( id= u.id, roles= me._get_roles( u, incl_holder= 'id')),
                )))

            #inexisting
            r = me.posts_qry_ass_exp( qry % dict( uid= -u.id),
                    exp= dict( user= dict(
                        flat= None,
                        nest= None,
                        )),
                    errors = [ dict(
                            path    = ['user', atr],
                            type    = 'DOES_NOT_EXIST',
                        ) for atr in ['flat', 'nest']
                    ])

        def test_all_count( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h2, 'MEMBER')
            m.Role.allow( me.u2, me.h2, 'MEMBER')

            qry = '''{ user {
                count %(filter)s
                all %(filter)s
                    { id %(ufields)s }
                all_count %(filter)s {
                    count
                    data
                        { id %(ufields)s }
                    }
            }}'''

            #flat, all
            users = q_as_odicts( objs( m.User), 'id', 'email')
            me.posts_qry_ass_exp( qry % dict( filter='', ufields='email'),
                    exp= dict( user=dict(
                        count = len( users),
                        all   = users,
                        all_count = dict( count = len( users), data = users,)
                        )) )

            #filtered 1
            uid = me.u1.id
            users1 = q_as_odicts( objs( m.User).filter( id=uid), 'id')
            me.assertEqual( len(users1), 1 )
            me.posts_qry_ass_exp( qry % dict( filter='( filter:{ id:%(uid)s })' % locals(), ufields=''),
                    exp= dict( user=dict(
                        count = 1,
                        all   = users1,
                        all_count = dict( count = 1, data = users1,)
                        )) )

            #inexisting
            me.posts_qry_ass_exp( qry % dict( filter='( filter:{ id:-%(uid)s })' % locals(), ufields=''),
                    exp= dict( user=dict(
                        count = 0,
                        all   = [],
                        all_count = dict( count = 0, data = [],)
                        )) )

            # nested, all
            users = q_as_odicts( objs( m.User), 'id', 'email', 'roles')
            for u in users:
                u['roles'] = q_as_odicts( u['roles'].all(), 'id', 'type')
            me.posts_qry_ass_exp( qry % dict( filter='', ufields= 'id email roles { id type }'),
                    exp= dict( user=dict(
                        count = len( users),
                        all   = users,
                        all_count = dict( count = len( users), data = users,)
                        )) )

    class filters( QLFuncs, tCommon, TestCase):
        CREATE_COUNTS = {
            m.Holder: 4,
        }

        def test_orderby( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            # m.Role.allow( me.u1, me.h2, 'MEMBER')
            m.Role.allow( me.u2, me.h1, 'OWNER')
            m.Role.allow( me.u2, me.h2, 'MEMBER')

            qry = '''{ role {
                default: all
                        { id type }
                id_down: all(
                    orderby: [ id__desc ])
                        { id type }
                type_up__id_up: all(
                    orderby: [ type, id])
                        { id type }
                type_down__id_up: all(
                    orderby: [ type__desc, id])
                        { id type }
            }} '''

            def order( *args):
                q = objs(m.Role).all() #.values( 'id','type' )
                return q_as_odicts( (q.order_by(*args) if args else q), 'id', 'type')

            exp = dict( role= dict(
                default         = order(),
                id_down         = order( '-id'),
                type_up__id_up  = order( 'type','id'),
                type_down__id_up = order( '-type','id'),
            ))
            me.posts_qry_ass_exp( qry, exp)

        def test_distinct( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h1, 'MEMBER')

            qry='''{ user {
                default: all(
                    filter: {roles: { holder: { id: %(hid)s}}})
                        { id }
                distinct: all( distinct: [],
                    filter: { roles: { holder: { id: %(hid)s}}})
                        { id }
            }} ''' % dict( hid= me.h1.id)

            #TODO: sql of this has orderby, but the qry below does not ???
            q = objs(m.User).filter( roles__holder= me.h1)
            exp = dict(
                default  = q.all(),
                distinct = q.distinct(),
            )
            me.posts_qry_ass_exp( qry, dict( user= qdict_as_odicts( exp, 'id')))

        def test_filter_by_manyto_rel(me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h1, 'MEMBER')
            m.Role.allow( me.u2, me.h1, 'OWNER')
            #m.Role.allow( me.u2, me.h1, 'OWNER')   #needs distinct
            m.Role.allow( me.u4, me.h1, 'OWNER')
            me.assertFalse( m.Role.objects.filter( user= me.u3).count())

            qry = '''{ user {
                noroles: all( filter:
                    {NOT: {roles: {} }})
                        {id }
                noroles_mmb: all( filter:
                    {NOT: {roles: {type: MEMBER }}})
                        {id }
                someroles: all( filter:
                    {roles: {} })
                        {id }
                someroles_mmb: all( filter:
                    {roles: {type: MEMBER }})
                        {id }
                eachroles_own: all( filter:
                    {roles__each: {type: OWNER }})
                        {id }
                eachroles: all( filter:
                    {roles__each: {} })
                        {id }
            }} '''

            q = objs( m.User) #.distinct()
            rel = m.User.roles.rel  #same as User._meta.get_field('roles').related_model
            assert rel.related_model is m.Role, rel.related_model
            assert rel.remote_field.name == 'user', rel.remote_field.name
            chk = dict(
                noroles         = q.filter( roles=None),
                noroles_mmb     = q.exclude( roles__type= m.Role._types.MEMBER),
                someroles       = q.exclude( roles=None),
                someroles_mmb   = q.filter( roles__type= m.Role._types.MEMBER),
                eachroles_own   = q.annotate( _hasothers= m.models.Exists(
                                        rel.related_model #m.Role
                                        .objects.filter( **{rel.remote_field.name: m.models.OuterRef('id')}
                                        ).exclude( type= m.Role._types.OWNER))
                                    ).filter( _hasothers=False,
                                            roles__type= m.Role._types.OWNER
                                    ),
                )
            chk = dict( (k,list(v)) for k,v in chk.items())
            exp = dict(
                noroles         = [ me.u3 ],
                noroles_mmb     = [ me.u2, me.u3, me.u4 ],
                someroles       = [ me.u1, me.u2, me.u4 ],
                someroles_mmb   = [ me.u1 ],
                eachroles_own   = [ me.u2, me.u4 ],
                )
            for x in chk,exp: x[ 'eachroles'] = x[ 'someroles']

            me.assertEqual( exp, chk)
            me.posts_qry_ass_exp( qry, dict( user= qdict_as_odicts( exp, 'id')))

        def test_pagination( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h2, 'MEMBER')
            m.Role.allow( me.u1, me.h3, 'MEMBER')
            m.Role.allow( me.u2, me.h1, 'OWNER')
            m.Role.allow( me.u2, me.h2, 'MEMBER')
            N = m.Role.objects.count()

            qry = '''{ role {
                first:          all( slice: { first: 2          } ) { id }
                first_skip:     all( slice: { first: 2, skip: 3 } ) { id }
                last_skip:      all( slice: { last : 2, skip: 3 } ) { id }
                last:           all( slice: { last : 2          } ) { id }
                first0:         all( slice: { first: 0          } ) { id }
                first0skip:     all( slice: { first: 0, skip: 1 } ) { id }
                last0:          all( slice: { last : 0          } ) { id }
                last0skip:      all( slice: { last : 0, skip: 1 } ) { id }
                skip_end_but1:  all( slice: { skip : %(N_1)s } ) { id }
                skip_end:       all( slice: { skip : %(N)s   } ) { id }
                skip_end_and1:  all( slice: { skip : %(N1_)s } ) { id }
                page1:          all( slice: { page: 1, perpage:4 } ) { id }
                page2:          all( slice: { page: 2, perpage:4 } ) { id }
                page3:          all( slice: { page: 3, perpage:4 } ) { id }
                limit_ofs_forw: all( slice: { offset:3,  limit: 2 } ) { id }
                limit_ofs_back: all( slice: { offset:-3, limit: 2 } ) { id }
            }}
            ''' % dict( N=N, N_1 = N-1, N1_=N+1)

            q = q_as_odicts( objs(m.Role), 'id')
            exp = dict( role= dict(
                    first           = q[:2],
                    first_skip      = q[3:],
                    last_skip       = q[:2:],
                    last            = q[-2:],
                    first0          = q,
                    first0skip      = q[1:],
                    last0           = q,
                    last0skip       = q[1:],    #XXX correct, last=0 -> dir defaults to forward
                    skip_end_but1   = q[N-1:],
                    skip_end        =  [], #q[N:]
                    skip_end_and1   = [],
                    page1           = q[:4],
                    page2           = q[4:],
                    page3           = [],
                    limit_ofs_forw  = q[3:],
                    limit_ofs_back  = q[:2:],
                ))
            me.posts_qry_ass_exp( qry, exp)

        @unittest.mock.patch.object( base, 'log_disabled', True)
        def test_pagination_errors( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h2, 'MEMBER')
            m.Role.allow( me.u1, me.h3, 'MEMBER')

            corrects = []

            corrects_as_is = [
                dict(),
                dict( page=1, perpage=1),
                ]
            corrects_optionals = [
                dict( first=1,skip=1),

                dict( last=1, skip=1),

                dict( offset=1,  limit=1),
                dict( offset=-1, limit=1),
                ]
            corrects = corrects_as_is + corrects_optionals
            for d in corrects_optionals:
                for n in d:
                    d0 = dict( d, **{n:0} )
                    if d0 not in corrects: corrects.append( d0)
                    dd = dict( (k,v) for k,v in d.items() if n != k )
                    if dd not in corrects: corrects.append( dd)
                    dd0 = dict( (k,0) for k in dd)
                    if dd0 not in corrects: corrects.append( dd0)
            for d in corrects_as_is + corrects_optionals:
                d00 = dict( (k,0) for k in d)
                if d00 not in corrects: corrects.append( d00)

            #for c in corrects: print(c)
            allnames = set(itertools.chain(*corrects))

            #print( allnames)

            triples = set( frozenset(x) for x in itertools.product( allnames, allnames, allnames) )
            tuples  = set( frozenset(x) for x in itertools.product( allnames, allnames) )
            singles = set( frozenset([x]) for x in allnames)
            a123 = singles | tuples | triples
            def fd( items): return tuple( tuple(i) for i in sorted(items))

            a123xp0n = set()
            for a in a123:
                a123xp0n.update( fd( zip( a,i))
                    for i in itertools.product( [0,1,-1], repeat=len(a)) )

            #print( len(a123xp0n))
            a123xp0n -= set( fd( d.items() ) for d in corrects )
            #print( len(a123xp0n))
            a123xp0n -= set( d for d in a123xp0n
                                if dict( (k,v) for k,v in d if v) in corrects
                                )
            #print( len(a123xp0n))

            for s in sorted( a123xp0n):
                #if s != (('first',0),): continue
                with me.subTest( s=s):
                    #print( s)
                    qry = '{ role { all( slice: { %(args)s }) { id } } }' % dict(
                                args= items2qlargs( s))
                    r = me.posts_qry_ass_exp( qry,
                            exp    = dict( role= dict( all= None)),
                            errors = [ dict(
                                path= ['role', 'all'],
                                type= 'INVALID_FILTER_ARGS',
                                )],
                            )
                    #break

        def test_empty_filter( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h2, 'MEMBER')

            qry = '''{ role {
                default     : all {id}
                empty       : all( filter: {}) { id }
                not_of_empty: all( filter: { NOT:{}}) { id }
            }}'''
            q = q_as_odicts( objs(m.Role), 'id')
            exp = dict( role= dict(
                    default         = q,
                    empty           = q,
                    not_of_empty    = q,    #XXX correct, whatever.. though purely logicaly would always return ()
                ))
            me.posts_qry_ass_exp( qry, exp)

        def test_and_or_not( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h1, 'MEMBER')
            m.Role.allow( me.u1, me.h2, 'MEMBER')
            m.Role.allow( me.u1, me.h2, 'OWNER')
            m.Role.allow( me.u1, me.h3, 'OWNER')

            fmt = dict( h1= me.h1.id, h2= me.h2.id, h3= me.h3.id )

            qry = '''{ role {
                filter_and_ss:      all( filter: {
                    AND: [
                        {holder: {id: %(h1)s} },
                        { type: OWNER }
                    ]}) { id }

                filter_ss:          all( filter: {
                    holder: {id: %(h1)s},
                    type: OWNER
                    }) { id }

                filter_not_s:       all( filter: {
                    NOT: { type: OWNER }
                    }) { id }

                filter_and_s_not_s: all( filter: {
                    AND: [
                        {NOT: {holder: {id: %(h1)s}} },
                        {type: MEMBER }
                    ]}) { id }

                filter_s_not_s:     all( filter: {
                    NOT: {holder: {id: %(h1)s}},
                    type: MEMBER
                    }) { id}

                filter_or_ss:       all( filter: {
                    OR: [
                        { holder: {id: %(h1)s}},
                        { holder: {id: %(h2)s }},
                        { type: OWNER}
                    ] }) { id }

                filter_or_s_not_s:  all( filter: {
                    OR: [
                        { holder: {id: %(h1)s }},
                        {NOT: { type: MEMBER }}
                    ] }) { id }

                filter_and_not_s_not_s: all( filter: {
                    AND: [
                        {NOT: { holder: {id: %(h1)s}}},
                        {NOT: { holder: {id: %(h2)s}}}
                    ] }) { id }

                filter_not_or_ss:   all( filter: {
                    NOT: {
                        OR: [
                            { holder: {id: %(h1)s}},
                            { holder: {id: %(h2)s}}
                    ]} }) { id }

                filter_not_s_in:    all( filter: {
                    NOT: {
                        holder: { id__cmp: { in: [ %(h1)s, %(h2)s ] }}
                    } }) { id }

                filter_not_not_s:   all( filter: {
                    NOT: {
                        NOT: { holder: { id: %(h3)s }}
                    } }) { id }

                filter_or_not_s_not_s: all( filter: {
                    OR: [
                        {NOT: {holder: { id: %(h1)s}}},
                        {NOT: {holder: { id: %(h2)s}}},
                    ] }) { id }

                filter_and_or_ss_or_ss: all( filter: {
                    AND: [
                        {OR: [ {holder: { id: %(h1)s}}, {holder: { id: %(h2)s}} ]},
                        {OR: [ {type: OWNER}, {type: MEMBER} ]}
                    ] }) { id }

                filter_or_and_ss_and_ss: all( filter: {
                    OR: [
                        { holder: { id: %(h1)s}, type: MEMBER },
                        {AND: [ {holder: { id: %(h2)s}}, {type: OWNER}]}
                    ] }) { id }
                filter_or_ss_ss:    all( filter: {
                    OR: [
                        { holder: { id: %(h1)s}, type: MEMBER },
                        { holder: { id: %(h2)s}, type: OWNER }
                    ] }) { id }
            }}''' % fmt

            q = objs( m.Role)
            def get_roles( q, *args):
                return q_as_odicts( (q.filter( *args) if args else q), 'id')

            f = dictAttr(
                h1o                 = get_roles( q, Q(holder= me.h1, type= 'OWNER')),
                not_h1_m            = get_roles( q.exclude( holder= me.h1).filter( type= 'MEMBER')),
                not_not_h3          = get_roles( q, ~Q( ~Q( holder= me.h3))),
                excl_owner          = get_roles( q.exclude( type= 'OWNER')),
                not_h1_or_not_h2    = get_roles( q.exclude( holder__in=[ me.h1, me.h2])),
                h2m                 = get_roles( q, Q(holder= me.h2, type= 'MEMBER')),
                h1_OR_h2_o          = get_roles( q, Q( holder__in= [ me.h1, me.h2]) | Q( type= 'OWNER')),
                h1_OR_not_m         = get_roles( q, Q( holder= me.h1) | ~Q( type= 'MEMBER')),
                or_not_h1_not_h2    = get_roles( q, (~Q( holder= me.h1) | ~Q( holder= me.h2))),
                h1m_or_h2o          = get_roles( q, Q( holder= me.h1, type='MEMBER') | Q( holder= me.h2, type='OWNER')),
                h1_or_h2_and_m_or_o = get_roles( q, Q( holder__in= [ me.h1, me.h2]) & Q( type__in=[ 'OWNER', 'MEMBER']))
            )
            exp = dict( role= dict(
                filter_and_ss       = f.h1o,
                filter_ss           = f.h1o,
                filter_not_s        = f.excl_owner,
                filter_and_s_not_s  = f.not_h1_m,
                filter_s_not_s      = f.not_h1_m,
                filter_or_ss        = f.h1_OR_h2_o,
                filter_or_s_not_s   = f.h1_OR_not_m,
                filter_and_not_s_not_s  = f.not_h1_or_not_h2,
                filter_not_or_ss    = f.not_h1_or_not_h2,
                filter_not_s_in     = f.not_h1_or_not_h2,
                filter_not_not_s    = f.not_not_h3,
                filter_or_not_s_not_s   = f.or_not_h1_not_h2,
                filter_and_or_ss_or_ss  = f.h1_or_h2_and_m_or_o,
                filter_or_and_ss_and_ss = f.h1m_or_h2o,
                filter_or_ss_ss         = f.h1m_or_h2o,
            ))

            me.posts_qry_ass_exp( qry, exp)

        def test_nested_fk_attr( me):
            h, c  = m.create_company_holder( me.u1, cm.company_srlz, rcomp= True)
            c.data = 'zzCompany'
            c.save()
            m.Role.allow( me.u1, me.h1, 'OWNER')
            me.assertEqual( m.Role.objects.count(), 2)

            qry = '''{ role {
                all( filter: {
                    holder: { company: { data: "%(c)s"}}}
                ) { holder { id company { id data } }}
            }}''' % dict( c= c.data)

            me.posts_qry_ass_exp( qry, exp = dict( role= dict(
                all= [ dict( holder= odict( id= h.id, company= odict_obj( c, 'id', 'data'))) ]
                )))


    class comparators( QLFuncs, tCommon, TestCase):
        CREATE_COUNTS = {
            m.Holder: 4,
        }
        def test_str_cmp( me):
            emails = ['1@trala.com', 'abcdx@aZ.bg', 'AZ@YY.COM', 'az@yy.com']
            for i in range( 1, 5):
                u = getattr( me, f'u{i}')
                u.email = emails[i-1]
                u.save()
                me.assertEqual( objs(m.User).get( id= i).email, emails[i-1])

            now = datetime.datetime.now()
            yesterday = now - datetime.timedelta( days=1)

            qry= '''{ user {
                email_contains:                     all( filter: { email__cmp: { contains: "tra"}} ) { id }
                email_contains_ignorecase_lower:    all( filter: { email__cmp: { ignorecase: true,  contains: "az"}} ) { id }
                email_contains_ignorecase_upper:    all( filter: { email__cmp: { ignorecase: true,  contains: "AZ"}} ) { id }
                email_contains_ignorecase_mixed:    all( filter: { email__cmp: { ignorecase: true,  contains: "aZ"}} ) { id }
                email_contains_matchcase_mixed:     all( filter: { email__cmp: { ignorecase: false, contains: "aZ"}} ) { id }
                email_contains_matchcase_lower:     all( filter: { email__cmp: { ignorecase: false, contains: "az"}} ) { id }

                email_eq_ignorecase:        all( filter: { email__cmp: { ignorecase: true,  eq: "%(u3email)s"}} ) { id }
                email_eq_ignorecase_mixed:  all( filter: { email__cmp: { ignorecase: true,  eq: "%(u2email)s"}} ) { id }
                email_eq_matchcase:         all( filter: { email__cmp: { ignorecase: false, eq: "%(u4email)s"}} ) { id }
                email_eq_ignorecase_upper:  all( filter: { email__cmp: { ignorecase: true,  eq: "%(u3email)s"}} ) { id }
                email_eq_matchcase_upper:   all( filter: { email__cmp: { ignorecase: false, eq: "%(u3email)s"}} ) { id }

                email_startswith:           all( filter: { email__cmp: { startswith: "abc"}} ) { id }

                email_eq:       all( filter: { email__cmp: { eq: "%(u1email)s" }}) { id }
                email_in:       all( filter: { email__cmp: { in: ["%(u1email)s", "%(u2email)s"]}}){ id }
                email_regex:    all( filter: { email__cmp: { regex: "1@...la"}}) { id }
                id:             all( filter: { id: %(u1id)s }) { id }
                id_eq:          all( filter: { id__cmp:    { eq: %(u1id)s }}) { id }
                id_in:          all( filter: { id__cmp:    { in: [ %(u1id)s, %(u2id)s ] }}) { id }

                created:        all( filter: { created: "%(u2created)s"}) { id }
                created_gt:     all( filter: { created__cmp: { gt: "%(yesterday)s"}}) { id }
                created_lt:     all( filter: { created__cmp: { lt: "%(yesterday)s"}}) { id }
            }}''' % dict(
                u1email = me.u1.email,
                u2email = me.u2.email,
                u3email = me.u3.email,
                u4email = me.u4.email,
                u1id    = me.u1.id,
                u2id    = me.u2.id,
                now         = drf_dt2str( now),
                u2created   = drf_dt2str( me.u2.created),
                yesterday   = drf_dt2str( yesterday)
            )

            q = q_as_odicts( objs(m.User), 'id')
            exp = dict( user= dict(
                email_contains                  = [ q[0]],
                email_contains_ignorecase_lower =   q[1:],
                email_contains_ignorecase_upper =   q[1:],
                email_contains_ignorecase_mixed =   q[1:],
                email_contains_matchcase_mixed  =   q[1:], #?
                email_contains_matchcase_lower  =   q[1:],
                email_eq_ignorecase             =   q[2:],
                email_eq_ignorecase_mixed       = [ q[1]],
                email_eq_matchcase              =   q[3:],
                email_eq_ignorecase_upper       =   q[2:],
                email_eq_matchcase_upper        = [ q[2]],
                email_startswith                = [ q[1]],
                email_eq                        = [ q[0]],
                email_in                        =   q[:2],
                email_regex                     = [ q[0]],
                id                              = [ q[0]],
                id_eq                           = [ q[0]],
                id_in                           =   q[:2],
                created                         = [ q[1]],
                created_gt                      =   q,
                created_lt                      = [],
            ))
            me.posts_qry_ass_exp( qry, exp)

        def test_expr( me):
            with me.subTest( name= 'id_eq_expr'):
                qry = '''{ user {
                    all( filter: {
                        id__cmp: { eq__expr: "13+id-10-3"}
                        }) { id }
                }}'''
                me.posts_qry_ass_exp( qry, exp = dict( user= dict(
                    all = q_as_odicts( objs(m.User), 'id'),
                    )))

            with me.subTest( name= 'dt_expr'):
                assert len(me.users) >= 3
                for d,u in enumerate( me.users.values(), -1):
                    dt = datetime.timedelta( days=d)
                    u.last_login = u.created + dt
                    u.save()
                qry = '''{ user{
                    all( filter: {
                        last_login__cmp: { eq__expr: "created"}
                        }) { id }
                }}'''
                exp1 = dict( user= dict(
                    all= q_as_odicts( objs(m.User).filter(
                            last_login= m.models.F('created')
                            ), 'id', ),
                ))
                exp = dict( user= dict(
                    all= q_as_odicts( [ me.u2 ] , 'id', ),
                ))
                me.assertEqual( exp1, exp)
                me.posts_qry_ass_exp( qry, exp)

            with me.subTest( name= 'bools'):
                me.u1.is_active = me.u1.is_superuser = False
                me.u1.save()
                qry = '''{ user{
                    bools_expr: all(
                        filter: { is_superuser__cmp: { eq__expr: "is_active"}
                        }) { id }
                    id_bool_expr: all(
                        filter: { id__cmp: { eq__expr: "id * is_active"}
                        }) { id }
                }}'''
                exp1 = dict( user= dict(
                    bools_expr= q_as_odicts( objs(m.User).filter(
                            is_superuser = m.models.F('is_active')
                            ), 'id', ),
                    id_bool_expr= q_as_odicts( objs(m.User).filter(
                            id = m.models.F('is_active') * m.models.F('id')
                            ), 'id', ),
                ))
                exp = dict( user= dict(
                    bools_expr= q_as_odicts( [ me.u1 ] , 'id', ),
                    id_bool_expr= q_as_odicts( [ u for u in me.users.values() if u is not me.u1] , 'id', ),
                ))
                me.assertEqual( exp1, exp)
                me.posts_qry_ass_exp( qry, exp)

        def test_rel( me):
            me.assertFalse( m.Role.objects.count())
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h1, 'MEMBER')
            m.Role.allow( me.u1, me.h2, 'MEMBER')
            m.Role.allow( me.u1, me.h2, 'OWNER')
            m.Role.allow( me.u1, me.h3, 'OWNER')

            qry = '''{ holder {
                rel_cmp_in: all( filter: {
                    roles: {
                        type__cmp: {
                            in: [ MEMBER]
                        }}
                    }) { id }
            }}''' % dict( h1id= me.h1.id)
            exp = dict( holder= dict(
                rel_cmp_in=  q_as_odicts( objs(m.Holder).filter( roles__type='MEMBER'), 'id'),
            ))
            me.posts_qry_ass_exp( qry, exp)

        def test_both_x_x_cmp( me):
            m.Role.allow( me.u1, me.h1, 'OWNER')
            qry = '''{ role { all(
                    filter: {
                        id: %(uid)s,
                        id__cmp: { eq: %(uid)s
                        }}
                    ) { id }
                }}''' % dict( uid= me.u1.id)
            exp = dict( role= dict( all= None ))
            overlap = 'id'
            me.posts_qry_ass_exp( qry, exp, errors= [ dict(
                message = f'cannot have both x:.. and x{_cmpsfx}:.. : {overlap}',
                path    = ['role', 'all'],
                type    = 'INVALID_FILTER_ARGS',
                )])


    class complex( QLFuncs, tCommon, TestCase):
        CREATE_COUNTS = {
            m.Holder: 3,
            m.Truck: 2,
        }
        def test_complex_query( me):
            t = me.truck1h2
            m.Role.allow( me.u1, me.h1, 'OWNER')
            m.Role.allow( me.u1, me.h2, 'OWNER')
            m.Role.allow( me.u1, me.h1, 'PERFORMER', m.any.Asset)
            m.Role.allow( me.u2, me.h2, 'PERFORMER', t)
            m.Role.allow( me.u2, me.h3, 'PERFORMER', m.any.Asset)

            anytruck = m.any.Truck.__class__.__name__
            anyasset = m.any.Asset.__class__.__name__
            role = 'PERFORMER'
            qry = '''{ user {
                u2_sees_truck: all( distinct:[], filter: {
                    OR: [
                        { roles: { asset: { holder: { id: %(ahid)s }}, type: %(role)s, holder: { id: %(h3id)s }}},
                        { roles: {                                     type: %(role)s, holder: { id: %(h2id)s }}},
                    ]
                }) { id email }
            }}''' % dict( role= role, h3id= me.h3.id, h2id= me.h2.id, ahid = m.any.Holder.id,
                          anytruck= anytruck, anyasset= anyasset)

            q = objs( m.User).filter(
                  Q( roles__asset__holder= m.any.Holder, roles__type= role, roles__holder= me.h3)
                | Q(                                     roles__type= role, roles__holder= me.h2)
                ).distinct()
            exp = q_as_odicts( q, 'id', 'email')
            exp1= q_as_odicts( [ me.u2 ], 'id', 'email')
            me.assertEqual( exp1, exp)
            me.posts_qry_ass_exp( qry, exp= dict( user= dict( u2_sees_truck= exp)))

# vim:ts=4:sw=4:expandtab
