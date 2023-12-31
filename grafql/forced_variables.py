
if 0*'alt1= str-pop xx from query-vars':
    class VarPopping_GraphQLView( GraphQLView):
        def execute_graphql_request( self, request, data, query, variables, *a,**ka):
            xx = variables.pop('xx', None)
            request.popping_variables = dict( xx=xx)
            query = query.replace('($xx:Int)','')   #XXX better use regex, with/out spaces|commas/Int|ID
            #print( 88788, variables, query)
            return super().execute_graphql_request( request, data, query, variables, *a,**ka)
    GraphQLView = VarPopping_GraphQLView

    def get_forced_varfiables( ctx):
        return ctx['info'].context.popping_variables

else:
    if 0*'alt2= ignore xx as variable_definition in NoUnusedVariables rule':
        from graphql.validation.rules import NoUnusedVariables
        #these are being cached by metaclass.. into _enter_handlers _leave_handlers etc so a) hack it there  b) remove NoUnusedVariables from rules  c) stop it reporting error
        _leave_OperationDefinition = NoUnusedVariables.leave_OperationDefinition
        def leave_OperationDefinition( self, *a,**ka):
            self.variable_definitions = [ v for v in self.variable_definitions if v.variable.name.value != 'xx']
            return _leave_OperationDefinition( self, *a,**ka)
        if 0*'doesnot work because metaclass':
            NoUnusedVariables.leave_OperationDefinition = leave_OperationDefinition
        else:
            for k,v in NoUnusedVariables._leave_handlers.items():
                if v is _leave_OperationDefinition:
                    NoUnusedVariables._leave_handlers[k] = leave_OperationDefinition

    elif 1*'alt3= remove NoUnusedVariables rule':
        try:    #gql<3.x
            from graphql.validation.rules import NoUnusedVariables, specified_rules
            specified_rules.remove( NoUnusedVariables)
        except ImportError:
            #gql=3.x
            from graphql.validation.specified_rules import specified_rules, NoUnusedVariablesRule
            s = set( specified_rules) - set([ NoUnusedVariablesRule ])
            import graphql
            import graphql.validation
            import sys
            m3 = sys.modules['graphql.validation.validate']         # WTF self-obscuring-names
            m4 = sys.modules['graphql.validation.specified_rules']  #
            for m in [ graphql, graphql.validation, m3,m4]:
                m.specified_rules = s
            #print( 777777, sorted(e.__name__ for e in graphql.specified_rules))


    def get_forced_variables( ctx):
        return ctx['info'].variable_values

if 0*'example':
    from svd_util.grafql.base import Resolver
    def ensure_current_handler( me, ctx):
        ctx.holder_on_behalf = get_forced_variables( ctx).get( 'h') #current_handler
        #assert current user belongs to holder_on_behalf
    Resolver.preparers.append( ensure_current_handler)

# vim:ts=4:sw=4:expandtab
