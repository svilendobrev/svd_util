from common_helpers.ql.base import metainfo_get
from common_helpers.dicts import dictAttr
from pprint import pprint
from common_helpers.dicts import fix_pprint_dictOrder
fix_pprint_dictOrder()

if 10:
    from api.ql.get import _types   #XXX FIXME WTF XXX

    _typenames = sorted( v.__name__ for v in _types.values())
    #print('================ ql._types')
    #pprint( _types)
    #print( '==== read roots2types')
    #print( *_typenames)
    _typename2model = dict( (v.__name__,m) for m,v in _types.items())
    #print( 11, *sorted(_typename2model))

    def getfields( types, typename):
        return types[ typename ][ 'fields']
    def getqlroots( ii, types, type):
        q = ii.get( type)
        if not q: return
        roots = getfields( types, q['name'])
        for t in roots.values():
            unnoise( t)
            fix_args( t)
        return roots
    def dictify( d, key):
        if d.get(key):
            dkey = d[ key]
            if isinstance( dkey,dict):
                a = dkey
            else:
                a = d[ key] = dict( (f['name'],f) for f in dkey)
            return a
    '''
        {..
           'name': 'prefetch_related',
           'type': {'kind': 'LIST',
                    'name': None,
                    'ofType': {'kind': 'ENUM',
                               'name': 'Deal_flds_tomany',
                               'ofType': None}}},
          {..
           'name': 'slice',
           'type': {'kind': 'INPUT_OBJECT',
                    'name': 'Pagination',
                    'ofType': None}}],
        'supplier': { ...
              'name': 'supplier',
              'type': {'kind': 'NON_NULL',
                       'name': None,
                       'ofType': {'kind': 'OBJECT',
                                  'name': 'Holder',
                                  'ofType': None}}},

        'items': { ..
               'name': 'items',
               'type': {'kind': 'LIST',
                        'name': None,
                        'ofType': {'kind': 'OBJECT',
                                   'name': 'DealItem',
                                   'ofType': None}}},

        ->{ name: prefetch_related
            type: Deal_flds_tomany
            kind: LIST
          { name: slice
            type: Pagination
            //tkind: INPUT_OBJECT ?
          { name: supplier
            type: Holder
            required: true
            kind: NON_NULL
            //tkind: OBJECT ?
          { name: items
            type: DealItem
            kind: LIST

          {'name': 'related_deals',
           'type': {'kind': 'LIST',
                    'name': None,
                    'ofType': {'kind': 'SCALAR',
                               'name': 'ID',
                               'ofType': None}}}],

          {'name': 'related_issues',
           'type': {'kind': 'NON_NULL',
                    'name': None,
                    'ofType': {'kind': 'LIST',
                               'name': None,
                               'ofType': {'kind': 'SCALAR',
                                          'name': 'ID',
                                          'ofType': None}}}}],
    '''
    def ofType( a):
        if not isinstance( a, dict): return a
        t = a['type']
        if not isinstance( t, dict): return dict( type= t)

        #if a.get('name')=='items':
        #    print( 62222222)
        #    pprint( t)
        r = {}
        if t.get('kind') == 'NON_NULL':
            r['kind'] = 'NON_NULL'
            t = t['ofType']
        if t.get('kind'):
            r['kind'] = ' '.join( x for x in [ t['kind'], r.get('kind')] if x)
        #ver<2.5 : t is [RelateTo] ; v>=2.5 : t is [RelateTo!]!  ,  so LIST X -> NON_NULL LIST NON_NULL X
        tt = t.get('ofType') or {}
        if tt.get('kind') == 'NON_NULL':
            t = tt['ofType']
        r = dict( r, type= (t.get('ofType') or {} ).get('name') or t['name'],
                     **(dict( description= a['description']) if a.get('description') else {}),
                     )
        #if r.get('type')=='CategoryItem':
        #    print( 7999999)
        #    pprint( a)
        #    pprint( t)
        #    pprint( r)
        #    print( 9999999)
        return r
    def unnoise1( f):   #copy
        return dict( ((k,f[k]) for k in 'args name'.split() if k in f), **ofType(f))
    def unnoise( f):    #inplace
        dels = set( f) - set( 'args name type fields kind description inputFields'.split())
        for k in dels: del f[k]
        if 'type' in f:
            f.update( ofType(f))
    def fix_args( ff):
        args = dictify( ff, 'args')
        if args:
            for aname,a in args.items():
                args[ aname] = ofType(a)
    def iswrap(t):
        return isinstance( t, str) and t.startswith('w_') #or t.startswith('qwrap_'))

    def fields2types( fields, types):
        r = {}
        for k,f in fields.items():
            type = f['type']
            description = f.get('description')
            #assert bool(iswrap( type)) == bool( metainfo_get( description).get( 'wrapper'))
            if iswrap( type):
                r[k] = (types[ type],description)
            else:
                r[k] = (f,description)  #type
        return r

    def fix_fieldtype( field, types, rtypes_flat =None, path =(), description =None):
        #if not isinstance( field, dict): return     #/me
        ff = field.get('fields') or ()
        DBG =0
        # /somemodel { all_count { .. } all { .. } one { .. } ... }
        # /vmrs { ck1 ck2 .. }
        # /me { x y .. _q { .. } }  but me is User
        # /other { x y .. _q { .. } }  but me is User

        if 'all' in ff:       # /root-types - iswrap
            if DBG: print( 3333, path)
            rff = ff['all']
            unnoise( rff)
            fix_args( rff)
            if not rff.get('args'):
                rff = rff['type']
            field.clear()
            field.update( rff)

            if rtypes_flat is not None: rtypes_flat[ '.'.join( path) ] = field

        elif ff or 'inputFields' in field:  # /vmrs  .._flt  all-plain-types
            if DBG: print( 4444, path, field.get('type'), field.get('name'))
            unnoise( field)
            if not ff and 'inputFields' in field:   #*_flt..
                ff = field['fields'] = field.pop( 'inputFields')
            if isinstance( ff, (list,tuple)):   #inputFields..
                ff = field['fields'] = dict( (f['name'],f) for f in ff )
            for k,f in (ff or {}).items():
                if not isinstance( f, dict): continue
                unnoise( f)
                fix_args( f)
                if DBG: print( 44441, k,f)
                if 0 and f.get('args'):
                    if DBG: print( 4448, k, f)
                    continue
                if 'type' not in f: continue
                tdef = f['type']
                if not iswrap( tdef):
                    if DBG: print( 44442, tdef, f)
                    if 0 and tdef != 'ID':    #keep links as-is plz
                        description = f.get('description')
                        type = tdef
                        if description:      #keep description
                            tdef = dict( type= tdef, description= description)    # ff[k] = f
                        ff[k] = tdef    # ff[k] = f
                    if iswrap( field.get('type') or field.get('name')):
                        if DBG: print( 44445, path, k, field)
                        if rtypes_flat is not None: rtypes_flat[ '.'.join( tuple( path) + ( k,)) ] = f#ield

                    continue
                t = types[ tdef].copy()
                ff[k] = t
                fix_fieldtype( t, types, rtypes_flat, tuple( path) + ( k,) )    #recursive
                #if rtypes_flat is not None: rtypes_flat[ '.'.join( tuple( path) + ( k,)) ] = field
                if DBG: print( 44443, path, k, t)
            if DBG: print( 44447, path, field)

        else: #no fields , no inputFields
            #default is WITH schema
            noneed_schema = metainfo_get( description).get( 'no_schema')
            if noneed_schema:
                if DBG: print( 66666, path, description, field)
                return
            if DBG: print( 5555, path, field)
            unnoise( field)
            fix_args( field)
            if not field.get('type'):
                field['type'] = field['name']
            if 0: #not field.get('args'):
                rff = field['type']
                if isinstance( rff, str):
                    rff = dict( types[ rff], type= rff)
                field.clear()
                field.update( rff)
                unnoise( field)
            if rtypes_flat is not None: rtypes_flat[ '.'.join( path) ] = field
        if DBG: print( 9999, path)
        if DBG: pprint( field)

    def ql_schema( schema, DBG =0):
        r = dictAttr()
        if DBG: print('================ introspect')
        r.ii = schema.introspect()['__schema']
        r.types = types = dictify( r.ii, 'types')
        for t in types.values():
            dictify( t, 'fields')
        r.rootgets = getqlroots( r.ii, types, 'queryType')
        if DBG: pprint( r.rootgets)

        r.getfuncs_tree = fields2types( r.rootgets, types)
        if DBG: print( '==== getfuncs_tree')
        if DBG: pprint( r.getfuncs_tree)
        if DBG: print( '==== types')
        if DBG: pprint( r.types)
        r.getfuncs_flat = {}
        for fname,(field,description) in r.getfuncs_tree.items():
            fix_fieldtype( field, types, r.getfuncs_flat, [ fname ], description)
        if DBG: print( '==== get roots, getfuncs_tree')
        if DBG: pprint( r.getfuncs_tree)
        if DBG: print( '==== get roots, getfuncs_flat')
        if DBG: pprint( r.getfuncs_flat)

        #r.typename2getfuncnames = dict( (v.get('type', v),k) for k,v in r.getfuncs_flat.items() )
        r.typename2getfuncnames = dict( (v['type'],k) for k,v in r.getfuncs_flat.items() )

        if DBG: print( '==== get types')
        r.gettypes = dict( (k, types[ v['type'] ]) for k,v in r.getfuncs_flat.items() )
        for tname,tdef in r.gettypes.items():
            #if 'tegory' in tname.lower(): pprint( tdef)
            fix_fieldtype( tdef, types )
        if DBG: pprint( r.gettypes)
        #if DBG: pprint( r.gettypes['deal']['fields']['items'] )

        r.get2model = dict( (k,_typename2model[ v['type']] ) for k,v in r.getfuncs_flat.items()
                            if _typename2model.get( v['type']))   #XXX for plain String @ root
        #pprint( r.get2models)
        #assert 0
        if DBG: print( '==== mut roots')
        r.mutators = getqlroots( r.ii, types, 'mutationType')
        if DBG: pprint( r.mutators)

        return r

#TODO this + above is somewhat lousy..
def field_type_kind( field):
    if isinstance( field, str): type = field
    else: type = field.get('_type')  #this because wrapping below
    if not type: return
    if not isinstance( type, dict): #incl args etc
        return dict( type =type)
    if 'type' not in type and 'name' in type:   #_q is like this
        type = dict( type, type= type['name'])
    return type #dict( (k,type[k]) for k in 'type description kind'.split() if type.get(k))


class Gen4ql:

    def exclude_types( me, types): return types
    def exclude_fields( me, fields): return fields
    def exclude_needed_types( me): pass     #polymorphic interfaces? in forms

    def make_schemas( me):
        if me.EDITOR:
            types = me.exclude_types( me.qls.mutators)
        else:
            types = me.exclude_types( me.qls.gettypes)

        if me.EDITOR:
            intypes = {}
            #TODO this may go as needed_types/has_types ?
            for muname,mutype in types.items():
                args = mutype.get('args') or {}
                #if not args: continue
                for aname,atype in args.items():
                    atypename = atype['type'] if isinstance( atype, dict) else atype
                    argtype = me.qls.types[ atypename]
                    if argtype.get('kind') != 'INPUT_OBJECT': continue
                    argtype = dict( argtype)
                    #argtype.update( fields= argtype.pop( 'inputFields'))
                    intypes[ atypename] = argtype
                    fix_fieldtype( argtype, me.qls.types)
                    argtype['type'] = atypename

            types.update( intypes)

        has_types = set()
        def add_type( r):
            has_types.add( list(r.values())[0]['type'] )

        for rname, rtype in types.items():
            r = me.cfg4type( rtype, rname)
            if not r: continue
            yield r
            add_type(r)

        if 0*'_flt-types':
            if not me.EDITOR:
                f = me.make_gform()
                me.needed_types |= f.needed_types

        me.needed_types -= has_types
        me.exclude_needed_types()
        #print( 888, *sorted(me.needed_types))
        while me.needed_types:
            rtype = me.needed_types.pop()
            rname = 'intermediate-' + rtype
            rtype = dict( me.qls.types[ rtype ])
            fix_fieldtype( rtype, me.qls.types)
            r = me.cfg4type( rtype, rname, intermediate=True)
            if not r: continue
            yield r
            add_type(r)
            me.needed_types -= has_types

    def setup( me):
        super().setup()
        me.needed_types = set()

        me.cfg_templates( fieldklas2template = dict(    #types
            Date    = 'date',
            DateTime= 'datetime',
            Boolean = 'onoff',
            Int     = 'number',
            Float   = 'number_float',
            Decimal = 'number_float',
            String  = 'text',
            JSONString  = 'text',
            UUID    = 'text',
            **( dict(
                String_short    = 'textshort',
                String_long     = 'textlong',
                ) if me.EDITOR else {})
            ))
        me.cfg_templates( modelkind2template= dict(    #types
            money   = 'money',
            ))
        me.cfg_templates( fieldklasi4link= dict(    #types
            ID      = 'link',
            ))
    def by_field_klas_link( me, field, schema):
        type = field_type_kind( field)
        if not type: return
        type = type['type']
        return me._cfg.fieldklasi4link.get( type)

    def by_field_klas( me, field, schema):
        ftype = field_type_kind( field)
        if not ftype: return
        type = ftype['type']
        r = me._cfg.fieldklas2template.get( type)
        #P = field['field_name']=='only_in_activities'
        #if P: print( 2222, field, type,r, ftype)
        d = ftype.get( 'description')
        dmeta = metainfo_get( d)
        dmeta.pop('help', '')
        if dmeta:
            if dmeta.get('kind'):
                rr = me._cfg.modelkind2template.get( dmeta['kind'])
                if rr: r = rr
            if type == 'String':
                assert r
                size = dmeta['size']
                if size=='None':
                    type += '_long'
                    size = None
                else:
                    size = int(size)
                    #if size<20: type += '_short'
                rr = me._cfg.fieldklas2template.get( type)
                if rr: r = rr
                if not isinstance( r, dict):
                    r = dict( f= r)
                r['size'] = size
            if dmeta.get('determined'):
                if not isinstance( r, dict):
                    r = dict( f= r)
                r['determined'] = dmeta['determined']
        #if P: print( 2233, r)
        if r: return r

        typql = me.qls.types.get( type )
        if not typql: return

        typqlkind = typql.get( 'kind')
        if typqlkind == 'ENUM':
            field._choices = [ v[ 'name'] for v in typql[ 'enumValues']]    #if not isDeprecated
            return me.templates[ 'choice' ]     #so its values_type = 'string', but alsocheck qltype, ql-enums go without quotes
        #if P: print( 2244, typqlkind, field)
        if (
            typqlkind in ['INPUT_OBJECT', 'OBJECT', 'INTERFACE']
            or me.qls.typename2getfuncnames.get( type)
            ):
            return me.templates[ 'object']
        #print( 2255, )
        #XXX why not just 'object'/choice' ??

    def templates( me):
        t = super().templates()
        def object( field):
            return dict(
                totype= field_type_kind( field)['type'],  #?same as qltype
                )

        l = dict( locals())
        del l['t']
        del l['me']
        return dict( t, **l)

    def strctx( me):
        return ' '.join( [ me.ctx.rname, me.ctx.rtypename ])

    def cfg4type( me, rtype, rname, intermediate= False):
        rtypename = rtype.get('type') or rtype.get( 'name')
        result = dict( type = rtypename,)

        if me.EDITOR:
            fields = rtype.get('args') or rtype.get('fields') or {}  #inputFields
            model = None
        else:
            fields = rtype['fields']
            model = me.qls.get2model.get( rname)
            if intermediate:
                assert not model
                model = _typename2model.get( rtypename)

            NO_q=0
            if NO_q: # no _q
                fields = dict( (k,v) for k,v in fields.items()
                            if not (isinstance(v,dict) and v.get('fields')) )

        me.ctx = dictAttr( rname= rname, rtype= rtype, rtypename= rtypename, model= model )
        if not me.EDITOR:
            if not intermediate:
                getfunc_args = me.qls.getfuncs_flat[ rname].get('args') or {}
                args = dict( (k, me.qls.types.get( v['type']))
                            for k,v in getfunc_args.items())
                for k,argtype in args.items():
                    if 'inputFields' in argtype:
                        argtype.update( fields= argtype.pop( 'inputFields'))
                    if argtype['fields']:
                        fix_fieldtype( argtype, me.qls.types)

                f = me.make_gform()
                f.ctx = dictAttr( rname= rname+'-args', rtype= '-args', rtypename= '-args', model= None)
                afields = dict( (k, dictAttr( field_name=k, _type=v['type'], **(dict( description= v['description']) if v.get('description') else {})))
                                for k,v in getfunc_args.items())
                aschema = f.schema_for_fields(
                            dict( (k,v) for k,v in afields.items()
                                if k not in 'filter slice'.split()
                            ))
                affields = args.get( 'filter', {})
                ffields = affields.get( 'fields', {})
                ffields = me.exclude_fields( ffields)

                fschema = f.schema_for_fields(
                            dict( (k,dictAttr( field_name=k, _type=v))
                                for k,v in ffields.items()
                                if k not in 'AND NOT OR'.split()
                            ))

                #pprint( aschema)
                #pprint( fschema)
                result.update( (k,v['values'] if v['template'] == 'choice' else v) for k,v in aschema.items() ) #if v['template'] == 'choice')
                if fschema:
                    result.update( filter= dict( (k,v) for k,v in fschema.items() if v['template'] != 'unknown'))

        fields = me.exclude_fields( fields or {})
        fields = dict( (k,dictAttr( field_name=k, _type=v)) for k,v in fields.items())
        resource_name = rname
        return { resource_name : dict(
                    me.conf( fields,
                        resource_name= not intermediate and resource_name or '',
                        resource     = not intermediate and resource_name or '',
                        #**extra_conf_kargs
                        ),
                    **result
                    )
                }

    def field2child_if_many( me, field, schema):
        tk = field_type_kind( field)
        if 'LIST' in (tk.get('kind') or '').split(): return field

    def field2totype_if_link( me, field, schema):
        if schema._ctx.modelfield:
            return super().field2totype_if_link( field, schema)

        tk = field_type_kind( field)
        totype = tk['type'] =='ID' and (tk.get('description') or '').startswith('of:') and tk['description'].split('of:',1)[1]
        if totype:     #HACK differ arg/ID from arg/ID depending on type it links to ... made in ql.mut.ID()
            totype,*attrs = totype.split(':')
            schema.update( totype = totype )
            if 'primary' in attrs:
                schema._ctx.primary_key = True
            return totype

    def make_schema( me, field, schema):
        tk = field_type_kind( field)
        schema._ctx.type_kind = tk
        r = super().make_schema( field, schema)
        r.update( qltype= tk['type'])
        totype = r.get( 'totype')
        if totype and r.template == 'object': #not in ( 'link', 'selflink', 'nomencl' ): #and not r.get('composite')):
            me.needed_types.add( totype)
        if r.qltype == 'String' and r.name =='search_text':
            columns = metainfo_get( field.get('description')).get('columns') or ''
            r.columns = columns.split(',')
        if r.name == 'orderby': #no more separate __desc
            r.values = [ x for x in r.values if not x.endswith('__desc')]
        return r

    def field2model_field( me, field, schema):
        if not me.ctx.model: return
        try:
            return me.ctx.model._meta.get_field( field.field_name)
        except me._cfg.FieldDoesNotExist: return

    def field2choices( me, field): return field._choices
    #def conf( me, fields, resource_name, **ka):

'''
ql/get:
    id: link+totype
    relation: object+totype;many
ql/put:
    id: selflink+totype
    relation: link+totype
    subobj: object+totype;many

DRF/get:
    id: number
    relation: link/linkmany+totype;many
    todo: subobj: object+totype;many DealItem_srlz
    no writeonly
    todo: DealItem..: /deal/id/dealitem/... from field.totype ? missing subviewset ?
DRF/put:
    #id: number  : readonly=gone
    relation: link+totype
    todo: subobj: link/linkmany+totype;many DealItem_srlz   from field-types-missing
    no readonly
'''

# vim:ts=4:sw=4:expandtab
