from django.test import TestCase, override_settings
from svd_util.django.models import DUMP
from .test_ql import odict, q_as_odicts, QLFuncs, shut_up, odict_obj, objs, tCommon

#TODO: someth involving auth, mufield/deco, error.whatever

from .models import Role, User, WrongInputError, assert_correct_input

#from svd_util.grafql.base import unrequire, dorequire, get_field, log, id2obj, id2idobj, error, get_request
#from svd_util.grafql.mut import _mutate, mufield, mufield_deco, obj_update, assert_permission, ID_required, ID_optional, Noresult
from svd_util.grafql import base,mut
@mut.mufield_deco( Role, args= dict(
                user    = mut.ID_required(),
                type    = base.dorequire( base.get_field( Role, 'type')),
                level   = base.unrequire( base.get_field( Role, 'level')),
            ),  id2obj=True)
def role_make( ctx, user, type, level =None):
    assert_correct_input( level < 5, 'too big level')
    return Role.create( user=user, type=type, level=level)


if 1:
    class mutators( QLFuncs, tCommon, TestCase):
        def posts_qry_ass_OK( me, qry):
            resp = me.posts_qry( qry)
            me.ass_resp_OK_json( resp)
            return resp

        def test_role_make( me):
            ka = dict(
                    user    = 1,#me.u1.pk,
                    type    = 'PERFORM',
                    level   = 3,
                    )
            qry = '''mutation {
                        role_make( user: %(user)s, level: %(level)s, type: "%(type)s", )
                    { id } }''' % ka
            resp = me.posts_qry_ass_OK( qry) #TODO MAYBE remove ass_OK

            qset = objs( Role).filter( **ka)
            me.assertEqual( qset.count(), 1)
            me.posts_qry_ass_exp( qry, exp= dict( role_allow= q_as_odicts( qset, 'id')[ 0]))
if 0:
    class m2( mutators):
        @shut_up
        def test_role_disallow( me):
            ka = dict(
                    user    = me.u1,
                    asset   = me.truck1h1,
                    holder  = me.h1,
                    type    = 'PERFORMER',
                    )
            def get_qry( base_qry, case, **ka):
                ka_ids = dict( (k, getattr( v, 'id') if k != 'type' else v) for k,v in ka.items())
                ka_qry = dict( (k, f'{k}: {v}' if k in case else '') for k,v in ka_ids.items())     #? k+':'+str(getattr( v, 'id') if k != 'type' else v)
                return base_qry % ka_qry

            from itertools import combinations, chain
            vars = [k for k in ka if k != 'type']

            for case in chain( [[]], *[ combinations( vars, 1+i) for i in range( len( vars)) ] ):
                with me.subTest( case=case):
                    empty = not case
                    case = list( case) + [ 'type']
                    objs( m.Role).delete()
                    me.assertEqual( objs( m.Role).count(), 0)

                    r = m.Role.allow( **ka)
                    me.assertEqual( objs( m.Role).count(), 1)

                    base_qry= '''mutation {
                                role_disallow( %(user)s, %(asset)s, %(type)s, %(holder)s )
                        }'''
                    qry = get_qry( base_qry, case, **ka)
                    resp = me.posts_qry_ass_OK( qry)

                    what = 'role_disallow'
                    me.posts_qry_ass_exp( get_qry( base_qry, case, **ka),
                        exp= {what: None},
                        errors = None if not empty else [dict(
                            message= 'cannot disallow everything',
                            path= [what],
                            type= 'WRONG_INPUT'
                            )]
                        )
                    me.assertEqual( objs( m.Role).count(), empty)

        @shut_up
        def test_company_add( me):
            data = 'asd'
            qry = '''mutation {
                company_add( data: "%(data)s")
                { id }
            }''' % dict( data= data)

            me.posts_qry_ass_exp( qry,
                exp= dict( company_add= None),
                errors = [dict( message= 'AUTH_NEEDED', path= [ 'company_add'], type= 'AUTH_NEEDED' )]
                )

            me.front_posts_login( me.lname)

            resp = me.posts_qry_ass_OK( qry)

            qset = objs( m.Holder).filter( company__data = data)
            me.assertEqual( qset.count(), 1)
            me.posts_qry_ass_exp( resp, dict( company_add= dict( q_as_odicts( qset, 'id')[ 0]) ))

        @shut_up
        def test_company_edit( me):
            h = objs( m.Company).create( data= 'asd')
            new_data = 'bsd'

            #XXX Doesn't need login
            #resp = me.posts_qry_ass_OK( qry_valid)
            #me.ass_resp_error( resp, type= 'AUTH_NEEDED')
            #me.front_posts_login( me.lname)

            invalid_hid = h.id+1231241
            qry_invalid_h = '''mutation {
                company_edit( id: "%(id)s", data: "%(data)s")
                { id }
            }''' % dict( data= new_data, id= invalid_hid)

            me.posts_qry_ass_exp( qry_invalid_h,
                exp= dict( company_edit= None),
                errors = [dict(
                    message= 'Company matching query does not exist.',
                    path= [ 'company_edit'],
                    type= 'DOES_NOT_EXIST' )]
                )

            qry_valid_h = '''mutation {
                company_edit( id: "%(id)s", data: "%(data)s")
                { id }
            }''' % dict( data= new_data, id= h.id)

            resp = me.posts_qry_ass_OK( qry_valid_h)

            qset = objs( m.Company).filter( data = new_data)
            me.assertEqual( qset.count(), 1)
            me.posts_qry_ass_exp( resp, dict( company_edit= dict( q_as_odicts( qset, 'id')[ 0]) ))

        def test_deal_add( me):
            ka = dict(
                      recipient= me.h1.id,
                      recipient_asset= me.truck1h1.id,
                      supplier= me.h2.id,
                      supplier_asset= me.truck1h2.id,
                      )
            for kind in 'ORDER REQUEST OFFER'.split():
                ka.update( kind= kind)
                qry = '''mutation {
                    deal_add(
                        recipient: "%(recipient)s",
                        supplier: "%(supplier)s",
                        recipient_asset: "%(recipient_asset)s",
                        supplier_asset: "%(supplier_asset)s",
                        kind: %(kind)s
                    ) {id}}''' % ka

                resp = me.posts_qry_ass_OK( qry)

                qset = objs( m.Deal).filter( **ka)
                me.assertEqual( qset.count(), 1)
                me.posts_qry_ass_exp( resp, dict( deal_add= dict( q_as_odicts( qset, 'id')[ 0])))

                objs( m.Deal).delete()

        @shut_up
        def test_deal_edit_copy( me):
            #TODO LATER test state_changes, when current holder is available
            for kind in 'ORDER REQUEST OFFER'.split():
                for add_items in [True, False]:
                    exp_text = 'tralala'
                    d = me.make_deal(
                        supplier=  me.h1,
                        recipient= me.h2,
                        supplier_asset=  me.truck1h1,
                        recipient_asset= me.truck1h2,
                        kind= kind,
                        text= exp_text,
                        )
                    di = m.DealItem.objects.create( deal=d, text='a')
                    base_qry = '''mutation {
                            %(what)s(
                                id: "%(id)s",
                                text: "%(text)s",
                                add_items: %(add_items)s) {
                                id text items { id }
                                } }'''
                    invalid_did = d.id+1231241
                    ka = dict(
                              text= exp_text,
                              add_items= 'true' if add_items else 'false',
                              )
                    with me.subTest( what='deal_edit'):
                        what = 'deal_edit'
                        exp_text = 'edited_tralala'

                        ka.update( what= what, id= invalid_did, text= exp_text)
                        qry = base_qry % ka
                        me.posts_qry_ass_exp( qry,
                            exp= {what: None},
                            errors = [dict(
                                message= 'Deal matching query does not exist.',
                                path= [what],
                                type= 'DOES_NOT_EXIST' )]
                            )

                        ka.update( id= d.id)
                        qry = base_qry % ka
                        resp = me.posts_qry_ass_OK( qry)
                        exp_ka = dict( items= [ dict( id= f'{di.id}') ] if add_items else [] )
                        me.posts_qry_ass_exp( resp, { what: dict( id= f'{d.id}', text= exp_text, **exp_ka) })

                    with me.subTest( what='deal_copy'):
                        what = 'deal_copy'
                        exp_text = 'copied_blabla'

                        ka.update( what= what, id= invalid_did, text= exp_text)
                        qry = base_qry % ka
                        me.posts_qry_ass_exp( qry,
                            exp= {what: None},
                            errors = [dict(
                                message= 'Deal matching query does not exist.',
                                path= [what],
                                type= 'DOES_NOT_EXIST' )]
                            )

                        ka.update( id= d.id)
                        qry = base_qry % ka
                        resp = me.posts_qry_ass_OK( qry)

                        copied_d = objs( m.Deal).filter( text= exp_text).first()
                        copied_di = objs( m.DealItem).filter( deal= copied_d).first()

                        copied_di_id = getattr( copied_di, 'id', None)
                        assert add_items == bool( copied_di_id)

                        exp_ka = dict( items= [ dict( id= f'{copied_di_id}') ] if add_items else [] )
                        me.posts_qry_ass_exp( resp, { what: dict( id= f'{copied_d.id}', text= exp_text, **exp_ka) })

                    objs( m.Deal).delete()

        #TODO deal_set_state_at_current_holder_side(), when current holder is available


    class TestAssetOps( QLFuncs, tCommon):
        #model = None
        def setUp( me):
            me.obj_data = me.model.__name__+ '_data'
            me.CREATE_COUNTS = {
                m.Holder: 2,
                me.model: 2
                }
            super().setUp()

        def test_add( me):
            key = me.model._meta.model_name +'_add'
            qry = '''mutation {
                %(key)s( data: "%(obj_data)s", holder: %(holder)s ) { id }
            }''' % dict(
                key= key,
                obj_data= me.obj_data,
                holder= me.h1.pk,
                )

            me.posts_qry_ass_exp( qry, exp = lambda: {
                    key: dict( *q_as_odicts(
                        objs( me.model).filter( data= me.obj_data }), 'id'))
                    }
                )

        def test_del( me):
            obj_id = me.assets_by_holder_by_type[ 1][me.model][0].id
            key = me.model._meta.model_name +'_del'
            #TODO: add test for del unexisting
            qry = '''mutation {
                %(key)s( id: %(o_id)s)
            }''' % dict( key= key, o_id= obj_id)

            q = objs( me.model).filter( id= obj_id)
            me.assertTrue( q.exists())

            me.posts_qry_ass_exp( qry, exp = dict(
                **{key: None},
                ))
            me.assertFalse( q.exists())

        @shut_up
        def test_edit( me):
            key = me.model._meta.model_name +'_edit'
            obj_data = 'ZZ'+ me.obj_data
            o_id = me.assets_by_holder_by_type[ 1][me.model][0].id
            h_id = me.h1.id
            qry = '''mutation {
                %(key)s( id: %(o_id)s, holder: %(h_id)s, data: "%(obj_data)s") { id data }
            }'''

            q = objs( me.model).filter( id= o_id)
            exp = [ dict(x, data= obj_data) for x in q_as_odicts( q, 'id', 'data')]

            me.posts_qry_ass_exp( qry % dict(
                key= key, o_id= o_id, h_id= h_id, obj_data= obj_data),
                exp= { key: exp[0]})

            o_id = 999999
            me.posts_qry_ass_exp( qry % dict(
                key= key, o_id= o_id, h_id= h_id, obj_data= obj_data),
                exp= {key: None},
                errors= [ dict(
                    message= me.model.__name__ + ' matching query does not exist.',
                    path= [key],
                    type= 'DOES_NOT_EXIST'
                    )]
                )

    for model in m.all_assets():
        tmodel = type( 't_'+model.__name__.lower(), ( TestAssetOps, TestCase), dict(
            model= model
            ))
        locals()[ tmodel.__name__] = tmodel


    class t_user( QLFuncs, tCommon, TestCase):
        model = m.Truck
        CREATE_COUNTS = {
            m.Holder: 1,
            }
        #posts_qry_ass_exp   = mutators.posts_qry_ass_exp why?
        posts_qry_ass_OK    = mutators.posts_qry_ass_OK

        def test_user_get_or_create_personal_holder( me):
            qry = '''mutation {
                user_get_or_create_personal_holder { id }
            }'''
            key = 'user_get_or_create_personal_holder'

            me.assertEqual( me.u1.personal_holder, None)
            resp = me.posts_qry_ass_exp( qry, exp=
                {key: None},
                errors= [ dict(
                    message= 'AUTH_NEEDED',
                    path= [ key],
                    type= 'AUTH_NEEDED'
                )]
            )

            me.u1.email = 'test@abx.com'
            me.u1.save()
            me.front_posts_login( me.u1.email)

            holders = objs( m.Holder)
            me.assertEqual( holders.count(), 1)
            resp = me.posts_qry( qry)
            q = holders.get( personal_of_user= me.u1)
            me.assertEqual( holders.count(), 2)

            me.posts_qry_ass_exp( resp, exp= dict(
                user_get_or_create_personal_holder= odict_obj( q, 'id')
                ))
            me.assertEqual( holders.count(), 2)

            me.u1.is_active = False
            me.u1.save()
            me.posts_qry_ass_exp( resp, exp= dict(
                user_get_or_create_personal_holder= odict_obj( q, 'id')
                ))

        def test_user_self_disable( me):
            qry = '''mutation{
                user_self_disable
            }'''
            q = objs( m.User).filter( is_active= True)
            me.assertEqual( q.count(), 1)

            exp_err= [ dict(
                message= 'AUTH_NEEDED',
                path= [ 'user_self_disable'],
                type= 'AUTH_NEEDED'
            )]
            resp = me.posts_qry_ass_exp( qry, exp=dict(
                user_self_disable= None),
                errors= exp_err,
                quiet= True
            )
            me.assertEqual( q.count(), 1)

            me.u1.email = 'test@abx.com'
            me.u1.save()
            me.front_posts_login( me.u1.email)

            me.posts_qry_ass_exp( qry, exp= dict( user_self_disable= None) )
            me.assertEqual( q.count(), 0)

        #@shut_up
        def test_user_set_default_holder( me):
            base_qry = '''mutation {
                user_set_default_holder( holder: %(id)s )
                { id }
            }'''
            u = objs( m.User).create( email= me.lname)

            role_ka = dict( user= u, holder= me.h1, type= 'OWNER')
            m.Role.allow( **role_ka)
            me.posts_qry_ass_exp( base_qry % dict( id= me.h1.id),
                exp= dict( user_set_default_holder= None),
                errors = [dict(
                    message= 'AUTH_NEEDED',
                    path= ['user_set_default_holder'],
                    type= 'AUTH_NEEDED'
                    )]
                )
            objs( m.Role).delete()

            me.front_posts_login( me.lname)
            me.posts_qry_ass_exp( base_qry % dict( id= me.h1.id),
                exp= dict( user_set_default_holder= None),
                errors = [dict(
                    message= 'PERMISSION_DENIED',
                    path= ['user_set_default_holder'],
                    type= 'PERMISSION_DENIED'
                    )]
                )

            #this test should be on a lower level
            me.posts_qry_ass_exp( base_qry % dict( id= m.any.Holder.id),
                exp= dict( user_set_default_holder= None),
                errors = [dict(
                    message= 'holder cannot be any/selector',
                    path= ['user_set_default_holder'],
                    type= 'WRONG_INPUT'
                    )]
                )

            m.Role.allow( user= u, holder= me.h1, type= 'OWNER')
            me.posts_qry_ass_exp(
                base_qry % dict( id= me.h1.id),
                dict( user_set_default_holder= dict( id= str(u.id)))
                )

# vim:ts=4:sw=4:expandtab
