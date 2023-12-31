## filter without relay TODO:
# - fix pagination fields sorting - skip is not where first/last are
#+ prefetch_related: with *tomany
#+ filter interpretation
# ~ relation to-many:
#  + none,some filter/exists -> none= x.all( filter: { NOT:{ y: {..fltr/empty..} }}) , some = x.all( filter: { y: {..fltr/empty..}})
#  + each:filter    x where each of x.y[].z == 5    XXX annotate+exists+filter..
# - has_errors - via annotate ? TODO
# + expr: F('x')*2
#+ orderby: fieldnames asc/desc, no funcs, subrels  # maybe add _lower modifier to do Lower(fname) on strings..
#+ pagination: +skip:n +first:n +last:n +page:n +perpage:n    -after:cursor -before:cursor
#+ polymorphism: Asset.type -> enum     #useful for filtering, not needed for data (has __typename)
# -- __typename in filters - cannot, db/models doesnt know about it, use .type

#grammar config
#CMP_IS_SEPARATE_FIELD = True
IGNORECASE_IS_MODIFIER= 'ignorecase'    #this cannot express icontains='a' and startswith('b')          ..  needs And( [] )
EXPR_IS_MODIFIER    = False     #this cannot express contains='a' and startswith( F('name'))    ..  needs And( [] )
FILTER_ONLY = True
SEARCH_TEXT_FIELDS = False      #function( model) returning field-names
SEARCH_TEXT_QUERY  = None       #function( qs, search_text) returning qs

import graphene
import itertools
from svd_util.dicts import dictAttr
from svd_util.attr import get_attrib
from django.db import models
Q = models.Q

SEP = '__'  #models.query.LOOKUP_SEP
#.. models.sql.QUERY_TERMS  django_filters/conf.VERBOSE_LOOKUPS
# + isnull range
_eq   = 'exact'.split()
_gtlt = 'gt lt gte lte range'.split()
_text = 'exact contains startswith endswith regex'.split()
_date = 'year month day week_day quarter'.split()
_in   = 'in'
_expr = 'expr'    #eval?  + { gt_expr: 'x*2' }  vs  { gt: 13, expr: 'x*2' } ignoring the 13 and must have only one cmp except the expr
_exprsfx = SEP+_expr
_cmpsfx  = SEP+'cmp'

# postgres only:
#   search      = fulltext, see  django.contrib.postgres.search  / SearchVector..
#   trigram_similar
# modifiers, inbetween field and lookup: i.e. Transform/s
#   unaccent    = unaccented_comparison - postgres only
#   lower, upper, length - not registered by default

# models.*Field.class_lookups
qtype2lookups = {
    graphene.String:    _gtlt + _text + (not IGNORECASE_IS_MODIFIER)*['i'+x for x in _text] ,
    graphene.DateTime:  _eq + _gtlt,
    graphene.Date:      _eq + _gtlt,
    graphene.Int:       _eq + _gtlt,
    graphene.Float:     _eq + _gtlt,
    graphene.Boolean:   _eq ,
    }
try:
    qtype2lookups[ graphene.Decimal ] =  _eq + _gtlt
except AttributeError: pass

qtype2modifiers = {
    graphene.String:    [ IGNORECASE_IS_MODIFIER ], #unaccent lower upper length
    graphene.DateTime:  _date + 'date time hour minute second'.split(),
    graphene.Date:      _date,
    }

lookup2name = dict( exact= 'eq', range= 'range_incl')
name2lookup = dict( (v,k) for k,v in lookup2name.items())
assert len( name2lookup) == len( lookup2name)

from .base import inregistry, change_frozen_meta, AnyRegistry, error, metainfo_put
from .base import construct_fields
import copy

error.types.update( (k,k) for k in '''
    INVALID_FILTER_ARGS
    '''.split())

######


_cmps = {}
def make_comparer( typ): #field):
    typ_class = typ if isinstance( typ, type) else typ.__class__
    if issubclass( typ_class, (graphene.Enum, graphene.ID)):
        lookups  = _eq
        modifiers= ()
    else:
        lookups   = qtype2lookups.get( typ_class) or ()
        modifiers = qtype2modifiers.get( typ_class) or ()
    if not lookups and not modifiers: return typ

    tcmp = _cmps.get( typ_class)
    if not tcmp:
        tname = typ_class.__name__
        tcmp = type( tname+'_cmp', ( graphene.InputObjectType,), dict( [
                    (lookup2name.get(v,v), typ) for v in lookups
                    ] + [
                    (lookup2name.get(v,v), graphene.Boolean()) for v in modifiers
                    ] + [
                    (lookup2name.get(v,v)+_exprsfx, graphene.String()) for v in lookups if not EXPR_IS_MODIFIER
                    ],
                    **{  _in  : graphene.List( typ_class),},
                    **({ _expr: graphene.String() } if EXPR_IS_MODIFIER else {}),
                    ))
        if 0:   #cannot union of scalar + object. sadly
            tcmp = type( tname+_cmpsfx, ( graphene.Union,), dict(
                        Meta = dict( types= [ typ_class, tcmp] )
                        ))
        _cmps[ typ_class] = tcmp
    return graphene.InputField( tcmp)

def make_fields4filter( no_cmp =False, **name_types):
    r = dict( (name, graphene.InputField( typ)) for name,typ in name_types.items())
    if not no_cmp: r.update( (name + _cmpsfx, make_comparer( typ)) for name,typ in name_types.items())
    return r


#links ->InputField
from graphene_django import converter
def register_replace( myfunc):
    orgfunc = getattr( converter, myfunc.__name__)
    myfunc.orgfunc = orgfunc
    for djm,func in list( converter.convert_django_field.registry.items()):
        if func is orgfunc:
            converter.convert_django_field.register( djm, myfunc)
    return myfunc

@register_replace   #OneToOneRel
def convert_onetoone_field_to_djangomodel( field, registry=None):
    if not isinstance( registry, AnyRegistry):
        r = convert_onetoone_field_to_djangomodel.orgfunc( field, registry)
    else:
        def dynamic_type():
            _type = registry.get_type_for_model( field.related_model)
            return _type and graphene.InputField(_type)#, description=field.help_text)
        r = graphene.Dynamic( dynamic_type)
    r.conv = convert_onetoone_field_to_djangomodel
    return r

@register_replace   #ManyToManyField ManyToManyRel ManyToOneRel
def convert_field_to_list_or_connection( field, registry=None):
    if not isinstance( registry, AnyRegistry):
        r = convert_field_to_list_or_connection.orgfunc( field, registry)
    else:
        def dynamic_type():
            _type = registry.get_type_for_model( field.related_model)
            return _type and graphene.InputField(_type)#, description=field.help_text)
        r = graphene.Dynamic( dynamic_type)
    r.conv = convert_field_to_list_or_connection
    r.relmodel = field.related_model
    return r

def is_rel_tomany( field):
    r = getattr( field, 'conv', None) == convert_field_to_list_or_connection
    return r or getattr(field, 'generic_relation_tomany', None)

@register_replace   #OneToOneField ForeignKey
def convert_field_to_djangomodel( field, registry=None):
    if not isinstance( registry, AnyRegistry):
        r = convert_field_to_djangomodel.orgfunc( field, registry)
    else:
        def dynamic_type():
            _type = registry.get_type_for_model( field.related_model)
            return _type and graphene.InputField(_type, description=field.help_text)
        r = graphene.Dynamic( dynamic_type)
    r.conv = convert_field_to_djangomodel
    return r

### obj 2 input-obj

_ftypes = {}        #? same as inregistry.get_type_for_model
_efields = {}
_basesubtypes_enums = {}

def make_inmodel( model, polymorphic ={}, exclude_fields =(), modelname =None,
                  extra_orderby =(), extra_select_related =(), extra_prefetch_related =()):
    mname = modelname or model.__name__
    for parent,children in polymorphic.items():
        if model in children:
            exclude_fields = [ parent.__name__.lower()+'_ptr' ] + list( exclude_fields)
    iattrs = construct_fields( model, registry= inregistry, only_fields=(), exclude_fields= exclude_fields )

    if model not in _efields:
        if isinstance( extra_orderby, str): extra_orderby = extra_orderby.split()
        if isinstance( extra_select_related, str): extra_select_related = extra_select_related.split()
        if isinstance( extra_prefetch_related, str): extra_prefetch_related = extra_prefetch_related.split()
        efields_noorder = [ k for k,f in sorted( iattrs.items(), key= lambda kv: (kv[0] != 'id',kv[0]))   #menu-order
                            if not is_rel_tomany( f)
                            ]
        extra_orderby_excludes = [ a[1:] for a in extra_orderby if a[0]=='!']
        extra_orderby = [ a for a in extra_orderby if a[0]!='!']
        efields_order = sorted( itertools.chain( *(((k,k),(k+SEP+'desc','-'+k))
                            for k in efields_noorder + list( extra_orderby)
                            if k not in extra_orderby_excludes
                            )))
        efields_tomany  = [ k for k,f in sorted( iattrs.items() )
                                     if k != 'id'
                                     #if is_rel_tomany( f)
                                    ]

        e = _efields[ model] = dictAttr(
            plain   = graphene.Enum( mname+'_flds_plain',  [ (k,k) for k in efields_noorder]),
            orderby = graphene.Enum( mname+'_flds_order',  efields_order),
            )

        if extra_select_related: e.update(
            select_related = graphene.Enum( mname+'_flds_select_related',  [ (k,k) for k in extra_select_related] ),
            )
        if extra_prefetch_related: e.update(
            prefetch_related = graphene.Enum( mname+'_flds_prefetch_related',  [ (k,k) for k in extra_prefetch_related] ),
            )

        if efields_tomany: e.update(
            tomany  = graphene.Enum( mname+'_flds_tomany', [ (k,k) for k in efields_tomany]),
            )


    #un-require   moved to AnyRegistry.get_converted_field

    needs_type_enum = False
    if model in polymorphic and 'type' in iattrs:  #Interface
        needs_type_enum = model
    else:   #Union ?
        for parent,children in polymorphic.items():
            if model in children and parent not in _ftypes:
                needs_type_enum = parent
                break

    if needs_type_enum:
        base_types_enum = _basesubtypes_enums.get( needs_type_enum)
        if not base_types_enum:
            base_types_enum = graphene.Enum( needs_type_enum.__name__ + '_types',
                                [(m.__name__, m.__name__) for m in polymorphic[ needs_type_enum] ] )
            _basesubtypes_enums[ needs_type_enum] = base_types_enum
        iattrs['type']  = base_types_enum()

#    if model is models.Asset and 'type' in iattrs:  #Interface
#        iattrs['type']  = Asset_types_enum()
#    elif issubclass( model, models.Asset) and models.Asset not in _ftypes: #Union #'type' not in _ftypes[ models.Asset]._meta.fields:
#        iattrs['type']  = Asset_types_enum()

    #relations to-many: one/each
    rels2many = {}
    for k,f in iattrs.items():
        if is_rel_tomany( f):
            rels2many[ k +SEP+'each'] = f
    iattrs.update( rels2many)

    #lookups
    #if CMP_IS_SEPARATE_FIELD:
    cmps = {}
    for k,f in iattrs.items():
        cmp = make_comparer( f)
        if cmp is not f:
            cmps[ k+_cmpsfx ] = cmp
    iattrs.update( cmps)

    #sorting: see base / sorted_by_name / yank_fields_from_attrs hack
    ql_fmodel = type( mname+'_flt', ( graphene.InputObjectType,), dict( iattrs,
                        **make_filter( lambda _m=model: _ftypes[_m], filter=False,
                                            efields= _efields[ model])
                        ))
    #print( 99999, model, *ql_fmodel._meta.fields, iattrs, _efields[ model] )
    _ftypes[ model ] = ql_fmodel
    change_frozen_meta( ql_fmodel, connection = None, model = model,)
    inregistry.register( ql_fmodel)

    return ql_fmodel


####################

def prefixrel( obj, path):
    if isinstance( obj, dict):
        return dict( (path+SEP+k,v) for k,v in obj.items())
    return prefixQ( copy.deepcopy(obj), path+SEP)

def prefixQ( node, pfx):
    if hasattr( node, 'children'):
        node.children = [ (
            ((pfx + c[0],) + c[1:]) if isinstance( c, tuple) else prefixQ( c, pfx)
            ) for c in node.children ]
    return node

def subrel__each( model, k, obj):
    #print( 'subrel_each', locals())
    for p in k.split( SEP):
        rel = model._meta.get_field( p)
        model = rel.related_model
    if isinstance( obj, dict): obj = Q(**obj)
    #print( model, rel, rel.remote_field.name)
    def q_anno( q):
        pfxobj = prefixrel( obj, k)
        #print( 3333, locals())
        return q.annotate( _hasothers= models.Exists(
                        rel.related_model.objects.filter( **{ rel.remote_field.name: models.OuterRef('id')}
                        ).exclude( obj
                        ))
                ).filter( pfxobj, _hasothers=False
                )
    return q_anno

#interpret filter
#XXX always copy input filter-dict before pop-ping stuff from it...

class _Vardict( dict):
    def __getitem__( me, k):
        if k in me: return super().__getitem__( k)
        v = models.F( k)
        me[k] = v
        return v

def q_cmp( cmps):
    ftrans = {}
    all_modifiers = set( itertools.chain( *qtype2modifiers.values()))
    for k,ops in cmps.items():
        ops = dict(ops)
        isexpr = EXPR_IS_MODIFIER and ops.pop( _expr, False)
        ignorecase = IGNORECASE_IS_MODIFIER and ops.pop( IGNORECASE_IS_MODIFIER, False)
        modifiers  = [ op for op in list(ops) if op in all_modifiers and ops.pop( op,False) ]
        k = SEP.join( modifiers + [k])
        for op,v in ops.items():
            if not EXPR_IS_MODIFIER:
                isexpr = op.endswith( _exprsfx)
                if isexpr: op = op[:-len(_exprsfx)]
            if isexpr:  #XXX may allow python/sql injection
                assert isinstance( v, str), v
                vardict = _Vardict( __builtins__=None)
                v = eval( v, vardict, vardict)
                #TODO check vardict against schema?

            if op=='in' and ignorecase:
                # there's no iin... either OR( iexact(x)) or iregex( x|x...)
                op = 'iregex'
                v = '^(' + '|'.join(v)+')$'
                ftrans[ k+SEP+op ] = v
                continue
            op = name2lookup.get( op, op)
            if ignorecase: op = 'i'+op
            ftrans[ k+SEP+op ] = v
    return ftrans

import graphql
Undefined = getattr( graphql, 'UndefinedDefaultValue', None)
ll='+++ '

def had_suffix( k, sfx):
    r = k.rsplit( sfx,1)
    if len(r)==2 and not r[1]: return r[0]
def had_prefix( k, pfx):
    r = k.split( pfx,1)
    if len(r)==2 and not r[0]: return r[1]

def anno_has( model, k, v):
    print( '..anno_has', locals())
    def q_anno( q):
        qa = q.annotate( **{ '_has_'+k: models.Count( k )})
        return (qa.exclude if v else qa.filter)( **{ '_has_'+k: 0 })
    return q_anno

annos = dict(
    #each= ( lambda k, v: isinstance( v, dict) and had_suffix( k, SEP+'each'), subrel__each),
    has = ( lambda k, v: isinstance( v, (bool,type(None))) and had_prefix( k, 'has'+SEP), anno_has),
    )
class q_expr:
    def __init__( me, model):
        me.model = model
        me.annotates = []

    @classmethod
    def _q_op( klas, q_arg, expr_items, op ='and', toarg =True, path =''):
        qq = [ q_arg( f, path) if toarg else f
                for f in expr_items if f ]
        if not qq: return # {}
        if len(qq)==1: return qq[0]
        return Q( _connector= Q.OR if op=='or' else Q.AND, *qq)
    def q_op( me, expr_items, op ='and', toarg =True, path =''):
        return me._q_op( me.q_arg, expr_items, op, toarg, path)

        qq = [ me.q_arg( f, path) if toarg else f
                for f in expr_items if f ]
        if not qq: return # {}
        if len(qq)==1: return qq[0]
        return Q( _connector= Q.OR if op=='or' else Q.AND, *qq)

    def q_arg( me, filter, path =''):
        filter = dict(filter)
        #print( ll,111, filter, path)
        pathpfx = path and path+SEP or ''
        if 'filter' in filter:
            f = filter.pop( 'filter')
            assert not filter, filter
            assert not path, path
            if f is not None and f is not Undefined:
                filter = dict(f)

        NOT = filter.pop( 'NOT', None)
        AND = filter.pop( 'AND', ())
        OR  = filter.pop( 'OR', ())

        cmps = dict( (k[:-len(_cmpsfx)],filter.pop(k)) for k,v in list(filter.items()) if k.endswith( _cmpsfx))
        overlap = ' '.join( set(cmps) & set(filter))
        if overlap:
            raise error.INVALID_FILTER_ARGS( f'cannot have both x:.. and x{_cmpsfx}:.. : {overlap}')
        filter.update( q_cmp( cmps))

        #print( ll,110, filter, path)
        #nesting on relations .. if cur.level is relation: prefix all k in filter
        frels = []
        for k,v in list(filter.items()):
            if not isinstance( v, dict): continue   #XXX weak
            del filter[k]
            for ext in [ SEP+'each']:
                kk = had_suffix( k, ext)
                if kk:
                    func = globals()['subrel'+ext]
                    k = kk
                    if v:
                        v = me.q_arg( v)    #prefix done inside func
                        me.annotates.append( func( me.model, pathpfx+k, v))
                        break
                    #else: same as without _each
            else:
                if not v:
                    v = ~Q( **{ pathpfx+k: None})    #is something = not (is nothing)
                else:
                    v = me.q_arg( v, path= pathpfx+k)
                frels.append( v)

        for k,v in list(filter.items()):
            for matcher, func in annos.values():
                kk = matcher( k,v)
                if not kk: continue
                del filter[k]
                me.annotates.append( func( me.model, pathpfx+kk, v))

        #print( ll,777777, filter, frels, OR,AND,NOT)
        if filter or frels:
            if not filter and len(frels)==1:
                filter = frels[0]
            else:
                filter = Q( *frels, **{ pathpfx+k:v for k,v in filter.items()})

        #print( ll,1222, filter, NOT, 'path=', path)
        r = me.q_op( [ filter,
                    OR  and me.q_op( OR,  op='or', path= path) ,
                    AND and me.q_op( AND, path= path) ,
                    NOT and ~me.q_arg( NOT, path),
                    ], toarg=False)
        #print( ll,222, r)
        #l-=3
        return r


class Pagination( graphene.InputObjectType):
    #pagination spec: https://facebook.github.io/relay/graphql/connections.htm#sec-Pagination-algorithm
    #see also:
    # https://www.citusdata.com/blog/2016/03/30/five-ways-to-paginate/
    # https://slack.engineering/evolving-api-pagination-at-slack-1c1f644f8e12
    # graphql_relay.connection.arrayconnection.connection_from_list_slice: cursor seems just an opaqued offset
    # cursor has to be an opaqued (set-of-fields-as-of-orderby) of prev/next row outside current page
    #before  = graphene.ID(),   #fw @cursor
    #after   = graphene.ID(),   #bw @cursor

    first   = graphene.Int( description= 'forward limit (from-start), >0, 0/missing: unlimited ; use with :skip ; conflicts with :last, :page/perpage, :offset/limit')
    last    = graphene.Int( description= 'backward limit (from-end) , >0 ; use with :skip ; conflicts with :first, :page/perpage, :offset/limit')
    skip    = graphene.Int( description= 'offset, >=0, direction depends on :first/last, default: forward ; conflicts with :page/perpage, :offset/limit')

    offset  = graphene.Int( description= 'signed offset, i.e. forward or backward depending on sign, 0/missing = forward, conflicts with :first/last/skip, :page/perpage')
    limit   = graphene.Int( description= 'limit, >0, 0/missing = unlimited, further in direction of offset ; conflicts with :first/last/skip, :page/perpage')

    page    = graphene.Int( description= 'page-number, >0 (1-based forward), needs :perpage ; conflicts with :first/last/skip, :offset/limit')
    perpage = graphene.Int( description= 'page-size, >0, needs :page ; conflicts with :first/last/skip, :offset/limit')

    @staticmethod
    def apply( flags, q):
        if (flags.first and flags.last):
            raise error.INVALID_FILTER_ARGS( ':first conflicts with :last')
        if sum( bool(x) for x in (
            (flags.first or flags.last or flags.skip),
            (flags.page or flags.perpage),
            (flags.limit or flags.offset),
            )) > 1:
                raise error.INVALID_FILTER_ARGS( 'use either :first/last/skip , or :page/perpage, or :limit/offset; do not mix them')
        #check >=0
        for k in 'first last skip page perpage limit'.split():
            v = getattr( flags, k, None)
            if v and v<0:
                raise error.INVALID_FILTER_ARGS( f':{k} cannot be <0')

        if flags.first:
            if flags.skip:  q = q[ flags.skip:]
            q = q[ :flags.first]
        elif flags.last:
            q = q.reverse()
            if flags.skip:  q = q[ flags.skip:]
            q = q[ :flags.last]
            q = list( reversed( q))
        elif flags.skip:
            if flags.skip:  q = q[ flags.skip:]

        elif flags.offset or flags.limit:
            if flags.offset:
                if flags.offset<0:
                    q = q.reverse()
                    q = q[ -flags.offset:]
                else:
                    q = q[ flags.offset:]
            if flags.limit:  q = q[ :flags.limit]
            if flags.offset and flags.offset <0:
                q = list( reversed( q))

        elif flags.perpage or flags.page:
            if not (flags.perpage and flags.page):
                raise error.INVALID_FILTER_ARGS( ':page and :perpage need both be >0 to work')
            #if flags.page<0: flags.page += number-of-pages
            ofs = (flags.page-1) * flags.perpage
            q = q[ ofs : ofs + flags.perpage ]

        return q


def make_filter( ql_fmodel_or_model, filter =True, efields =None, pagination =True, search_text =True, export =False):
    '''
    AND: { x=1, y=2 }
    OR of ANDs:  { OR= [ { x=1 }, { x=2, .. } ] }
    AND of ORs: { AND= [
        OR= [ { x=1 }, { x_cmp={ gt: 2}, .. } ]
        OR= [ { y=1 }, { y=2, .. } ]
        ] }
    NOT of AND: { NOT= { x=1, y=2 } }
    NOT of OR:  { NOT= { OR=[ {x=1}, {x=2}] } }

    beware, all of them in one:
    {   x=1,
        OR = [ {x=2}, {x=3} ],
        AND= [ {x=4}, {x=5} ],
        NOT= {x=6},
    } means x=1 and (x=2 or x=3) and (x=4 and x=5) and not x=6
    and beware that its not like natural language, so:
    {   x=1,
        OR = [ {x=2} ],
    } means x=1 AND x=2 !!  maybe throw error here to avoid misunderstanding
    '''
    r = {}
    if isinstance( ql_fmodel_or_model, type) and issubclass( ql_fmodel_or_model, models.Model):
        ql_fmodel = lambda: _ftypes[ ql_fmodel_or_model]
        if not efields: efields = _efields[ ql_fmodel_or_model]
        model = ql_fmodel_or_model
    else:
        ql_fmodel = ql_fmodel_or_model
        model = get_attrib( ql_fmodel, '_meta.model', None)

    if filter:
        if not efields: efields = _efields[ model ]
        r.update(
            filter  = graphene.Argument( ql_fmodel), #default_value= graphql.Undefined ?? see fix_Argument_defaultvalue_to_Undefined
            orderby = graphene.List( efields.orderby),
            distinct= graphene.List( efields.plain, description= 'use empty list, non-empty is postgres only'),
            )
        if 'select_related' in efields:
            r['select_related'] = graphene.List( efields.select_related)
        if 'prefetch_related' in efields:
            r['prefetch_related'] = graphene.List( efields.prefetch_related)

        if pagination:
            r.update( slice= graphene.Argument( Pagination))
        if export:
            r['export'] = graphene.String( description= 'comma separated field names')
        if search_text and (SEARCH_TEXT_FIELDS or not model):   #forced, _flags below
            sfields = SEARCH_TEXT_FIELDS( model ) if model and callable( SEARCH_TEXT_FIELDS) else [ 'all-possible-fields' ]
            sfields = ','.join( sorted( sfields))
            if sfields:     #some model may be not searchable
                r.update( search_text = graphene.Argument( graphene.String, description= metainfo_put( columns=sfields)))

    if not FILTER_ONLY or not filter:
        r.update(
            AND = graphene.List( ql_fmodel),
            OR  = graphene.List( ql_fmodel),
            NOT = graphene.Argument( ql_fmodel),
            )
    return r

#zflags = 'orderby distinct slice select_related prefetch_related'.split()
_flags = set(
    make_filter( graphene.ID,
        efields= dictAttr(
            orderby= graphene.ID, plain= graphene.ID, tomany= graphene.ID,
            select_related= graphene.ID, prefetch_related= graphene.ID,
            ),
        filter=True, pagination=True, search_text=True, export=True)
    )
_flags -= set( 'AND OR NOT filter exporter export'.split())
#assert _flags == set(zflags)

def model_filter( query_or_model, kargs, with_count =False, parent =None, annotates_after_filter =(), ctx =None):
    if not isinstance( query_or_model, models.QuerySet):
        q = query_or_model.objects.all()
    else:
        q = query_or_model
    #print(3666666, q.model, ctx['info'].context.body)# for k in ctx['info'].__class__.__slots__), parent)#  kargs, parent)
    #print(3666666, q.model, dict((k, getattr( ctx['info'], k)) for k in ctx['info'].__class__.__slots__), parent)#  kargs, parent)
    kargs = dict(kargs)

    _export_fields = kargs.pop('export', None)
    exporter = kargs.pop('exporter', None)
    if exporter and _export_fields:
        export_url = exporter( _export_fields, q, kargs, ctx)
        return dictAttr( export_url= export_url)

    _selected = None
    if kargs.get('filter') and kargs['filter'].get('_selected__cmp'):
        _selected = kargs['filter'].pop('_selected__cmp')['in']

    flags = dictAttr( (k,kargs.pop( k, None)) for k in _flags)
    qexpr = q_expr( q.model)
    f = qexpr.q_arg( kargs)
    for afunc in qexpr.annotates:   #+annotates_before_filter maybe
        q = afunc(q)
    #print('   3666', f, dict((k,v) for k,v in flags.items() if v is not None))
    if f: q = q.filter( f)
    for afunc in annotates_after_filter:
        q = afunc(q)

    if flags.search_text and SEARCH_TEXT_FIELDS:
        sfields = SEARCH_TEXT_FIELDS( q.model ) if callable( SEARCH_TEXT_FIELDS) else True
        if sfields:     #some model may be not searchable
            #q = q.search_text( flags.search_text)
            q = SEARCH_TEXT_QUERY( q, flags.search_text)
    if flags.select_related:
        q = q.select_related( *flags.select_related)
    if flags.prefetch_related:
        q = q.prefetch_related( *flags.prefetch_related)
    if flags.orderby:
        _selected_orderby = None
        if '-_selected' in flags.orderby: _selected_orderby = '-_selected'
        if '_selected' in flags.orderby:  _selected_orderby = '_selected'
        if _selected_orderby:
            if _selected:
                q = q.annotate( _selected = models.Case( models.When( id__in= _selected, then=1), default=0, output_field= models.BooleanField()))
            else:
                flags.orderby.remove( _selected_orderby)

        q = q.order_by( *flags.orderby)
    if flags.distinct is not None and flags.distinct is not Undefined:
        q = q.distinct( *flags.distinct)    #beware of distinct+orderby-on-relation
    count = q.count() if with_count else None

    if flags.slice:
        q = Pagination.apply( flags.slice, q)
    if count is not None:
        q = dictAttr( count= count, data= q)
    return q

# vim:ts=4:sw=4:expandtab
