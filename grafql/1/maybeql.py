'''
if injection / ast-manipulation before-resolve is needed, see graphql.execution: execute_operation, and collect_fields for all inside operation
#query-injection.. is against the tide
middleware is at or after-resolve
'''

directives = None
if 0*'directives':
    from graphql import DirectiveLocation, GraphQLDirective, specified_directives
    predefined = GraphQLDirective(
        name = 'predefined',
        description = 'predefined stuff appended to query',
        args = {},
        locations = [ DirectiveLocation.QUERY,
            #DirectiveLocation.FRAGMENT_SPREAD,
            #DirectiveLocation.INLINE_FRAGMENT,
            ],
        )
    directives = specified_directives + [ predefined ]
    ...
    schema = graphene.Schema( query= qlQuery, directives= directives, auto_camelcase=False,)

middleware = None
if 0*'middleware':
    from promise import Promise
    dirs = dict( predefined=lambda val, *a,**ka: [val,print(8888, val)][0] )
    class CustomDirectivesMiddleware(object):
        def resolve(self, next, root, info, **kargs):
            result = next(root, info, **kargs)
            return result.then(
                lambda resolved: self.__process_value(resolved, root, info, **kargs),
                lambda error: Promise.rejected(error)
            )
        def __process_value(self, value, root, info, **kargs):
            new_value = value
            field = info.field_asts[0]
            for directive in field.directives or ():
                proc = dirs[ directive.name.value ]
                new_value = proc( new_value, directive, root, info, **kargs)
            return new_value
    middleware = [ CustomDirectivesMiddleware]
    ...
    url( '^graphql', GraphQLView.as_view( graphiql=True, schema= ql.schema, middleware=ql.middleware))


if 'filtering/relay':
    from graphene_django.filter import DjangoFilterConnectionField
    mtype2lookups = {
        models.models.CharField:        _text + ['i'+x for x in _text] + _gtlt,
        models.models.DateTimeField:    _eq + _gtlt, #year month day week_day  # date hour minute
        models.models.DateField:        _eq + _gtlt, #year month day week_day
        models.models.IntegerField:     _eq + _gtlt,
        }

    if 0 and model is models.Asset:
        class Asset_qlnode( graphene.Union):
            Meta= dict( types= [_nodes[a] for a in models.all_assets( asset=False, anyasset=True ) ]) #model= model,
        ql_node = Asset_qlnode
    else:
        ql_node = type( mname+'_qlnode', (DjangoObjectType,), dict( Meta= dict( model= model,
                interfaces= (graphene.relay.Node,),
                filter_fields= dict( (f.name, mtype2lookups.get( f.__class__, ['exact']))
                    for f in model._meta.concrete_fields)
                )))
    _nodes[ model ] = ql_node
    _query[ lname]  = graphene.relay.Node.Field( ql_node)
    _query[ lnames] = DjangoFilterConnectionField( ql_node, )#filterset_class=..
    #TODO: use somehow Meta4FilterSet: strict, filter_overrides
    #TODO: addfields, renames, etc from drf.srlzing/filters

# vim:ts=4:sw=4:expandtab
