#see testargs.py
import graphene
v3 = False
try:
    import graphql
    v3 = graphql.version.startswith('3.')
except AttributeError: pass

######## HACK fix Interface.resolve_type  ; Union also has one but it does not matter there
def fix_Interface_resolve_type():
    if v3: return #not used ; v3.x: from graphene.types.schema import TypeMap ; create_interface
    if not hasattr( graphene.Interface, 'resolve_type'): return
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

# XXX HACK fixes: remove named func-arguments to allow them in kargs i.e. arguments of the field
# see also get.ListResolver using the .my=org below

def fix_DjangoListField_list_resolver():
    from graphene_django.fields import DjangoListField
    org = DjangoListField.list_resolver
    newfunc = fix_any_resolve( DjangoListField, 'list_resolver')
    if newfunc: #else already done
        newfunc.my = org

# *Executor.execute
def fix_SyncExecutor_execute():
    try:
        from graphql.execution.executors.sync import SyncExecutor
    except: return  #v3
    if getattr( SyncExecutor.execute, 'my', 0): return
    SyncExecutor.execute = lambda *a,**kargs: a[1]( *a[2:], **kargs)
    SyncExecutor.execute.my=1
if 0:
    from graphql.execution.executors.thread import ThreadExecutor
    from graphql.execution.executors.gevent import GeventExecutor
    from graphql.execution.executors.asyncio import AsyncioExecutor
    from graphql.execution.executors.process import ProcessExecutor
    for ex in ThreadExecutor, GeventExecutor, AsyncioExecutor, ProcessExecutor, :
        ex.execute = lambda *a,**kargs: a[1]( *a[2:], **kargs)

from svd_util.dicts import dictAttr
def fix_any_resolve( klas, methodname):
    #DjangoDebugMiddleware.resolve: def resolve(self, next, root, info, **args):
    #DjangoListField.list_resolver:
    # graphene_django <  2.6: #def list_resolver( resolver, root, info, **args):
    # graphene_django >= 2.6: #def list_resolver( django_object_type, resolver, root, info, **args):
    # graphene_django >= 2.8: #def list_resolver(
    #                               django_object_type, resolver, default_manager, root, info, **args
    #                               ):
    #so:
    # - func2code3+byteplay .execode -> func-of-args-in-passed-locals()
    # + inspect.getsource, replace signature, add 1 line... :
    # def resolvefunc( what,ever,args, root, info, **kargsname):
    #   ->
    # def resolve( *_a, **kargsname):
    #    what,ever,args, root, info,  = _a

    method = getattr( klas, methodname)
    if getattr( method, 'my', 0): return

    import inspect
    #klas_method = getattr( klas, methodname)   #this see through staticmethod..
    klas_method = klas.__dict__[ methodname]
    if inspect.isfunction( klas_method):
        func = klas_method
        wrapper = None
    else:
        assert isinstance( klas_method, staticmethod), klas_method
        func = klas_method.__func__
        wrapper = staticmethod
    assert inspect.isfunction( func)
    module = inspect.getmodule( method)
    srclines,lineno = inspect.getsourcelines( method)
    #print( 333333, method)

    ix = 0
    defline = ''
    while ':' not in defline:
        defline += srclines[ix]
        ix += 1
    deffunc,args = defline.split('(',1)
    args,kargs = args.split('**')
    kargs = ' '.join( kargs.split())
    args = args.strip()
    funcdefs = deffunc.split()
    ixdef = funcdefs.index('def')
    predef = funcdefs[:ixdef]
    postdef= ' '.join( funcdefs[ ixdef+1:])
    if predef:
        assert ''.join( predef) == '@staticmethod', predef
    indent = ''
    for s in srclines[ix]:
        if s.isspace(): indent+=s
        else: break
    src = ''.join( [ f'''\
def {postdef}( *_a, **{kargs}
{indent}{args} = _a
''',
        #f'{indent}print( 188888888888, _a)\n',
        ] + srclines[ ix:])
    #print( src)
    def ex():
        namespace = {}
        exec( src, module.__dict__, namespace)
        assert len(namespace) == 1, namespace
        return namespace.popitem() #locals()
    newname,newfunc = ex()
    assert newname == methodname, (newname,methodname)
    if wrapper: newfunc = wrapper( newfunc)
    setattr( klas, newname, newfunc)
    newmethod = getattr( klas, newname)
    newmethod.my = 22
    return newmethod

def fix_DjangoDebugMiddleware_resolve():
    #from graphene_django import settings
    #settings.DEFAULTS[ 'MIDDLEWARE' ] = () #.. avoid whole
    from graphene_django.debug import DjangoDebugMiddleware
    fix_any_resolve( DjangoDebugMiddleware, 'resolve')

def fix_make_it_promise():
    from graphql.execution import middleware
    try:
        if getattr( middleware.make_it_promise, 'my', 0): return
    except AttributeError: return   #v3
    from promise import Promise
    middleware.make_it_promise = lambda *a,**b: Promise.resolve( a[0](*a[1:], **b))
    middleware.make_it_promise.my = 1

def fix_execute__on_rejected():  # exceptions are lost when promise is rejected and nothing gets logged
    if v3: return   #unknown
    from graphql.execution import executor as qlexecutor
    from graphql.execution import utils

    if not getattr( utils.ExecutionContext.report_error, 'my', 0):      #ExecutionContext.handle_field_error
        def report_error(self, error, traceback=None):
            # type: (Exception, Optional[TracebackType]) -> None
            if not getattr( getattr( error, 'original_error', None), 'kukurigu', None):
                exception = utils.format_exception(
                    type(error), error, getattr(error, "stack", None) or traceback
                )
                utils.logger.error("".join(exception))
            self.errors.append(error)
        report_error.my = 1
        utils.ExecutionContext.report_error = report_error

    if not getattr( qlexecutor.resolve_or_error, 'my', 0):
        if 10:
            import sys
            from .base import error

            def resolve_or_error(
                resolve_fn,  # type: Callable
                source,  # type: Any
                info,  # type: ResolveInfo
                args,  # type: Dict
                executor,  # type: Any
            ):
                # type: (...) -> Any
                try:
                    return executor.execute(resolve_fn, source, info, **args)
                except Exception as e:
                    log = utils.logger.exception
                    e2 = error.convert_exc( e) or e  # just to decide on logging severity level
                    if isinstance( e2, error.QLError) or e2 in error.types:
                        log = utils.logger.info
                    log(
                        "An error occurred while resolving field {}.{}".format(
                            info.parent_type.name, info.field_name
                        )
                    )
                    e.stack = sys.exc_info()[2]  # type: ignore
                    e.kukurigu = 1
                    return e
        else:
            orig_resolve_or_error = qlexecutor.resolve_or_error
            def resolve_or_error( *a, **ka):
                r = orig_resolve_or_error( *a, **ka)
                if isinstance( r, Exception):
                    r.kukurigu = 1
                return r
        resolve_or_error.my = 1
        qlexecutor.resolve_or_error = resolve_or_error

    if not getattr( qlexecutor.Promise, 'my', 0):
        # this to fix on_rejected func that's nested in execute (currently executor.py:126)
        class Promise( qlexecutor.Promise):
            my = 1
            def catch(self, on_rejection):
                if on_rejection.__name__ == 'on_rejected':
                    exe_context = on_rejection.__closure__[0].cell_contents
                    def fixed_on_rejected(error):
                        exe_context.report_error( error)  # so that the logger in report_error logs it
                    on_rejection = fixed_on_rejected
                return super().catch( on_rejection)
        qlexecutor.Promise = Promise

# attr_resolver / dict_resolver
def fix_attr_resolver():
    if v3: return
    from graphene.types import resolver
    if getattr( resolver.attr_resolver, 'my', 0): return
    resolver.attr_resolver = lambda *a,**kargs: getattr( a[2], a[0], a[1])
    resolver.dict_resolver = lambda *a,**kargs: a[2].get( a[0], a[1])
    resolver.default_resolver = resolver.attr_resolver
    resolver.attr_resolver.my=1
#beware of set_default_resolver there

def fix_Argument_defaultvalue_to_Undefined():
    try:    #v2-old
        from graphql.utils.undefined import UndefinedDefaultValue as UV
    except:     #v3
        from graphql import Undefined as UV

    if getattr( graphene.Argument, 'my', 0): return
    ainit = graphene.Argument.__init__
    def __init__( me, *a,**ka):
        ainit( me, *a,**ka)
        if me.default_value is None and 'default_value' not in ka:
            me.default_value = UV
    graphene.Argument.__init__ = __init__

    binit = graphene.InputField.__init__
    def __init__( me, *a,**ka):
        binit( me, *a,**ka)
        if me.default_value is None and 'default_value' not in ka:
            me.default_value = UV
    graphene.InputField.__init__ = __init__

    graphene.Argument.my = 1

def fix_get_argument_values_None():
    from graphql.execution import values
    if getattr( values.get_argument_values, 'my', 0): return
    values._get_argument_values = values.get_argument_values
    def get_argument_values( arg_defs, arg_asts, variables=None):
        result = values._get_argument_values( arg_defs, arg_asts, variables)
        if not arg_defs or not arg_asts: return result   #assume correct
        arg_ast_map = {
            arg.name.value: arg for arg in arg_asts
        }  # type: Dict[str, Argument]
        for name, arg_def in arg_defs.items():
            oname = arg_def.out_name or name
            if oname in result: continue
            arg_ast = arg_ast_map.get( name)
            if name not in arg_ast_map or isinstance( arg_ast.value, values.ast.Variable): continue    #assume correct
            arg_type = arg_def.type
            value = values.value_from_ast( arg_ast.value, arg_type, variables)
            if value is None:
                result[ oname] = value
        return result
    values.get_argument_values = get_argument_values
    values.get_argument_values.my = 1
    try:    #v < 3
        from graphql.execution import utils
        utils.get_argument_values = get_argument_values
    except ImportError:
        from graphql.execution import execute
        execute.get_argument_values = get_argument_values

#######
from graphene_django import converter
@converter.convert_django_field.register( converter.models.BooleanField)
def convert_field_to_boolean( field, registry =None):
    from svd_util.grafql.base import metainfo_put
    if field.null:
        return converter.Boolean( description= metainfo_put( help= field.help_text ))
    if field.has_default():     #XXX isnt this for all type of fields ????
        return converter.Boolean( description= metainfo_put( help= field.help_text, determined=True))
    return converter.NonNull(
               converter.Boolean, description= metainfo_put( help= field.help_text, determined=True))

def fix_create_enum_getattr_metadata():
    from graphene.types.schema import TypeMap, GraphQLEnumValue, GrapheneEnumType
    if getattr( TypeMap.create_enum, 'my', 0): return

    def create_enum( graphene_type):
        values = dict( (k, GraphQLEnumValue( value= v)) for k,v in graphene_type._meta.enum.__members__.items())
        type_description = (
            graphene_type._meta.description(None)
            if callable(graphene_type._meta.description)
            else graphene_type._meta.description
        )

        return GrapheneEnumType(
            graphene_type=graphene_type,
            values=values,
            name=graphene_type._meta.name,
            description=type_description,
            )
    TypeMap.create_enum = staticmethod( create_enum)
    TypeMap.create_enum.my = 1

def fix_Scalar_parse_literals():
    from graphql import GraphQLString
    from graphene import String, UUID, JSONString
    String.parse_literal = staticmethod( GraphQLString.parse_literal)  #original@String is wrong
    def parse_literal4json( node, *a,**ka):
        v = GraphQLString.parse_literal( node, *a,**ka)  #original@String is wrong
        return JSONString.parse_value( v)
    JSONString.parse_literal = staticmethod( parse_literal4json)
    def parse_literal4uuid( node, *a,**ka):
        v = GraphQLString.parse_literal( node, *a,**ka)  #original@String is wrong
        return UUID.parse_value( v)
    UUID.parse_literal   = staticmethod( parse_literal4uuid)


def fix_all_execute_resolve():
    if not v3:  #not used anyway, unknown how to replace
        fix_Interface_resolve_type()
    fix_DjangoListField_list_resolver()
    if not v3:  #because of args to resolvers seems okay?
        fix_SyncExecutor_execute()
        fix_make_it_promise()
        fix_attr_resolver()
    fix_DjangoDebugMiddleware_resolve() #this is same old code
    fix_Argument_defaultvalue_to_Undefined()
    fix_get_argument_values_None()
    if not v3:  #unknown
        fix_execute__on_rejected()
    else:
        fix_create_enum_getattr_metadata()
        fix_Scalar_parse_literals()

# vim:ts=4:sw=4:expandtab
