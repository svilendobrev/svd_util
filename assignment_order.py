#s.dobrev 2k4
"""
 Obtain order of assigments in python source text namespaces.

 python loses order at end of exec, as all namespaces
 are/must be plain dicts (set via PyDict_SetItem - there is only
 a temporary array of local vars in exec' frame in C).
 Handles assignment, class def, function def, import.
 Warning: conditional definitions etc runtime stuff is ignored -
          this goes through _all_ the source.

 update 2011: python3, class def order can be kept:
        class OrderedClass( type):
             @classmethod
             def __prepare__( metacls, name, bases, **kwds):
                return collections.OrderedDict()
             def __new__( cls, name, bases, classdict):
                result = type.__new__( cls, name, bases, dict( classdict))
                result.members = tuple(classdict)
                return result
        class A( metaclass= OrderedClass):
            .......................

use as:
    a = ASTVisitor4assign()
    klastree = a.parse( src_string1 )
    ###now use klastree (or a.klas which is same)
    klastree.pprint()

    a.parse( src_string2 )    #as if src = src_string1 + src_string2
    a.klas.pprint()
    ###for clean reuse, either do a.__init__() or make another ASTVisitor4assign

    ###for whole module:
    import xxx      #assume there's class X1 inside
    klastree = ASTVisitor4assign().parseModuleSource( xxx )
    klastree.set_order_in_namespace( xxx)   #,flatten=True to pre-calculate flattened order
    print xxx._order
    print xxx.X1._order

    ### put this at end of a module for self-auto-ordering (e.g. at import):
    try:
        _order
    except NameError:
        from util.assignment_order import ASTVisitor4assign
        ASTVisitor4assign().parseFile_of_module( __file__).set_order_in_namespace( globals(), flatten =True)
        #print '==================='
        #print _order

    ###get _all_ attribs of some class, ordered:
    for key,value in get_class_attributes_flatten_ordered( xxx.X1):
        print ' ', key,value

"""

# see compiler.visitor
# uses compiler.ast as parser.ast is too grammar specific.

_attr_filter__default = lambda a: a.startswith('__') and a.endswith('__')

class ASTVisitor4assign:
    """usage: create an instance, then run .parse*( src).
        a.parse( src1); a.parse( src2)  ===  a.parse( src1 + src2 )
    """


    class Klas:
        """ root instance of this is returned by ASTVisitor4assign.parse*().
        use set_order_in_namespace() to setattr a '_order' list into each class of the
        source class hierarhcy, assuming it exists as class object"""

        def __init__( me, name, type ='',
            ):
            me.name = name
            me.vars = []
            me._vars = {}  #fast search
            me.klasi = []
            me.all = []
            me.type = type

        def _add_var( me, name ):
            if name in me._vars:
                return True
            else:
                me.vars.append( name)
                me._vars[ name] = 1
                me.all.append( name)

        def _add_klas( me, klas ):
            #no check for duplicates!
            me.klasi.append( klas)
            me.all.append( klas.name)
            return klas

        _add_func = _add_var
        _add_import = _add_var

        def pprint( me, pfx ='', ):
            if me.all:
                print pfx, 'klas', me.type or '', me.name or '<>' , ':'
            pfx = pfx+'  '
            if 1:
                for var in me.vars:
                    print pfx, var
                for klas in me.klasi:
                    klas.pprint( pfx)
            else:
                for a in me.all:
                    if isinstance( a, me.__class__):
                        a.pprint( pfx)
                    else:
                        print pfx, var

        def set_order_in_namespace( me, namespace, order_name ='_order', flatten =False, with_classes =False,
                **kargs_flatten_class__order ):
            """ assign a '_order' list into each class of the hierarchy, assuming it exists as class object.
                namespace is the relevant (for me) class, module or dict (e.g. globals()
                which is same as __main__.__dict__).
                flatten=True will pre-calculate the flattened-hierarchy attribute list (_order_flat).
            """
            if type( namespace) is dict:
                _setattr = dict.__setitem__
                _getattr = dict.__getitem__
            else:
                _setattr = setattr
                _getattr = getattr
            if with_classes:
                order = me.all
            else:
                order = me.vars

#            print 'order:', _getattr( namespace, '__name__'), me.name, me.type or 'klas', order
            _setattr( namespace, order_name, order)

            for k in me.klasi:
                #print ' klas:', _getattr( namespace, '__name__'), k.name, k.type
                k_namespace = _getattr( namespace, k.name)
                k.set_order_in_namespace( k_namespace,
                                            order_name=order_name,
                                            flatten=flatten,
                                            with_classes=with_classes,
                                            **kargs_flatten_class__order )
                if flatten:
                    flatten_class__order( k_namespace,
                                            order_name=order_name,
                                            **kargs_flatten_class__order)

        def flatten_class__order( me, namespace, **kargs_flatten_class__order):
            _getattr = type( namespace) is dict and dict.__getitem__ or getattr
#            print ' flat:', _getattr( namespace, '__name__'), me.name, me.type or 'klas'
            if type( namespace) is not dict:
                flatten_class__order( namespace, **kargs_flatten_class__order)
            for k in me.klasi:
                k_namespace = _getattr( namespace, k.name)
                k.flatten_class__order( k_namespace, **kargs_flatten_class__order)

        def filter_order( me, namespace, attr_filter =None, order_filter =None, order_name ='_order' ):
            _getattr = type( namespace) is dict and dict.__getitem__ or getattr
            order = _getattr( namespace, order_name)
            if order_filter:
                order[:] = order_filter( order )    #replace
            else:
                todel = [ o for o in order if attr_filter(o) ]
                for o in todel:
                    order.remove(o)
            for k in me.klasi:
                k_namespace = _getattr( namespace, k.name)
                k.filter_order( k_namespace, attr_filter=attr_filter, order_filter=order_filter, order_name=order_name)


        def pprint_order_in_namespace( me, namespace, order_name ='_order', pfx='', **kargs_flatten_class__order ):
            """ namespace is the relevant (for me) class, module or dict
                (e.g. globals() which is __main__.__dict__)
            """
            if type( namespace) is dict:
                _getattr = dict.__getitem__
                print pfx,'<dict>:'
            else:
                _getattr = getattr
                print pfx,str(namespace)+':'
            pfx = pfx+'   '

            print pfx, '- order:'
            print pfx,' ', ', '.join( _getattr( namespace, order_name))
            import types
            if type( namespace) is dict or isinstance( namespace, types.ModuleType): pass
            else:
                print pfx, '- flattened order:'
                for k,v in get_class_attributes_flatten_ordered( namespace, **kargs_flatten_class__order):
                    print pfx,' ', k,'\t=',v

            for klas in me.klasi:
                k_namespace = _getattr( namespace, klas.name)
                klas.pprint_order_in_namespace( k_namespace, order_name=order_name, pfx=pfx, **kargs_flatten_class__order)

    def __init__( me,
                do_import =False,                   #bool
                do_function =None,                  #bool or include-matching-filter(name)
                do_visit_function =None,            #bool or include-matching-filter(name) - forces do_function=True
                attr_filter =_attr_filter__default,  #exclude-matching-filter(name) - applies over all attr types
                call_on_duplicates =None,
                klas_adder =None,                   #do-something( klas,parent); return klas-to-use4visit or None to skip
            ):
        #if attr_filter=='default': attr_filter = _attr_filter__default
        me.attr_filter = attr_filter or (lambda *a:False)
        me.call_on_duplicates = call_on_duplicates or (lambda *a:None)
        me.do_visit_function = callable( do_visit_function) and do_visit_function or (lambda *a:do_visit_function)
        me.do_function = callable( do_function) and do_function or (lambda *a:do_function)
        me.do_import = do_import
        me.add_klas = klas_adder or (lambda newklas, parentklas: parentklas._add_klas( newklas))
        #root:
        me.klas = me.Klas( '')

    def visitAssName( me, node):
        if node.flags != 'OP_ASSIGN': return
        #print node
        name = node.name
        if me.attr_filter( name): return
        if me.klas._add_var( name):
            me.call_on_duplicates( name, node, me )

    def visitClass( me, node):
        name = node.name
        if me.attr_filter( name): return
        #print 'klas', name
        me._visitClass( node)

    def _visitClass( me, node, **kargs):
        klas = me.klas
        newklas = me.Klas( node.name, **kargs)
            #what if same klas repeated.. bad luck
        newklas = me.add_klas( newklas, klas)
        #klas._add_klas( newklas)
        if newklas:
            me.klas = newklas       #push
            me.visit( node.code)    #call back the caller - indirect recursion
            me.klas = klas          #pop

    #all things inside funcs are usualy not of interest - too dynamic
    def visitFunction( me, node):
        name = node.name
        if not me.attr_filter( name):
            if me.do_visit_function( name):
                #print 'func', name
                me._visitClass( node, type='func')
            elif me.do_function( name):     #add as attr only
                #print 'func', name
                if me.klas._add_func( name):
                    me.call_on_duplicates( name, node, me )
                #me.visit( node.code)    #call back the caller - indirect recursion

    def visitImport( me, node):
        #print 'import', node.names
        if me.do_import:
            for mod_name, as_name in node.names:
                if as_name is None:
                    as_name = mod_name.split( '.',1)[0]
                if not me.attr_filter( as_name):
                    if me.klas._add_import( as_name):
                        me.call_on_duplicates( as_name, node, me )

    def visitIf( me, node):
        from compiler.ast import Const
        #print node.tests
        for test,stmt in node.tests:
            #print test
            if isinstance( test, Const) and (
                    test.value == 'NOT_FOR_ASSIGNMENT_ORDER'
                    or not test.value
                ):
                #print 'ignore', stmt
                pass
            else:
                me.visit( stmt)    #call back the caller - indirect recursion

    def visitFrom( me, node):
        #print 'from', node.modname, 'import', node.names, 'ignored'
        return me.visitImport( node)

    def parse( me, src):
        import compiler
        ast = compiler.parse( src +'\n')
        compiler.walk( ast, me )
        return me.klas

    def parseFile( me, path):
        import compiler
        ast = compiler.parseFile( path)
        compiler.walk( ast, me )
        return me.klas

    def parseModuleSource( me, module):
        """ Warning: module's .__file__ attribute may be pathname of
            precompiled .pyc, .pyo, shared library .so/.dll/.. for C extensions,
            or not available at all if module is statically linked into interpreter.
            These are all checked but Something may escape through...
        """
        try:
            src_filename = module.__file__
        except AttributeError:      #statically linked builtin
            raise TypeError, 'cannot access sourcefile for '+ str(module)
        return me.parseFile_of_module( src_filename)

    def parseFile_of_module( me, src_filename):
        """ Warning: module's .__file__ attribute may be pathname of
            precompiled .pyc, .pyo, shared library .so/.dll/.. for C extensions,
            or not available at all if module is statically linked into interpreter.
            These are all checked but Something may escape through...
            just set env PYTHON_PATH / sys.path for strange-places
            DO NOT imp.find_module()!
        """
        #can use inspect.getsourcefile( config), but this is a bit better
        fl = src_filename.lower()   #to lower() or not??
        import imp
        for suffix, mode, kind in imp.get_suffixes():
            if fl[-len(suffix):] == suffix:
                if kind == imp.PY_COMPILED:
                    src_filename = src_filename[:-len(suffix)] + '.py'  #guess? lower/upper-case??
                elif kind != imp.PY_SOURCE:
                    # not text file
                    raise TypeError, 'cannot access sourcefile for '+ str(module)
                break
        return me.parseFile( src_filename) #hope for accessible, syntacticaly correct, source file

    def parseClassSource( me, klas):
        import inspect, textwrap
        return me.parse( textwrap.dedent( inspect.getsource( klas)))



def flatten_class__order( klas, order_name ='_order', flat_name ='_order_flat',
                            ignore_missing_order =False,
                            attr_filter =_attr_filter__default,
            _used =None ):

    """collect and set order of _all_ attributes of (hierarchical) class as class.flat_name """
    #if attr_filter=='default': attr_filter = _attr_filter__default
    #ignore cached _order_flat when computing
    if _used is None:   #root
        try:
            #return getattr( klas, flat_name)   #this looks through into bases!
            return klas.__dict__[ flat_name ]
        except (AttributeError, KeyError): pass
        _used = {}   #global for root
    _used_klas = _used
    _used_vars = {}     #local!

    try:
        order = getattr( klas, order_name)
    except AttributeError:
        if not ignore_missing_order: raise
        order = ()

    o = []
#    if 'CM' in klas.__name__:
#        print '1', klas, type( klas), type(klas)==type #, klas.__class__
    try:
        #if klas.__class__ is type: return o    #klas is a type-object
        if type( klas) is type: return o        #klas is a type-object
        if issubclass( klas, type): return o    #klas is a type-object
    except AttributeError: pass                 #non-object/old-style classes have no __class__

    #recursion, deep then wide...
    for base in klas.__bases__:
#        if 'CM' in klas.__name__:
#            print 'base', base.__name__, base._order
        if base not in _used_klas:              #base duplicates ignored
            _used_klas[ base] = 1
            r = flatten_class__order( base, order_name=order_name, flat_name=flat_name,
                                        ignore_missing_order=ignore_missing_order,
                                        attr_filter=attr_filter,
                                        _used=_used )
#            if 'CM' in klas.__name__:
#                print 'base2', base.__name__, base._order
            for a in r:
                if a not in _used_vars:         #vars duplicates ignored
                    #? if not attr_filter or not attr_filter(a):
                    o.append( a)
                    _used_vars[a] = 1       #local

    #print '2', klas, _used_vars, o
    for a in order:     #do not ignore missing _order
        if a not in _used_vars:             #vars duplicates ignored
            if not attr_filter or not attr_filter(a):
                o.append( a)
                _used_vars[ a] = 1          #local
    setattr( klas, flat_name, o )
    #print '3', klas, _used_vars, o, order
    return o

def get_class_attributes_flatten_ordered( klas, inst =None, **kargs_flatten_class__order):
    """ordered yield attr,value for _all_ attributes of (hierarchical) class/instance
        no results/AttributeError until iterated !
    """
    if inst is None: inst = klas
    for a in flatten_class__order( klas, **kargs_flatten_class__order ):
        yield a, getattr( inst, a)


def test( module, src_filename =None, flatten =True, print_tree =False):
    a = ASTVisitor4assign()
    if not src_filename:
        klastree = a.parseModuleSource( module)   #try guess the source file
    else:
        assert module
        klastree = a.parseFile_of_module( src_filename)   #hope for accessible, syntacticaly correct, source file

    if print_tree:
        print module, 'tree:'
        klastree.pprint()

    klastree.set_order_in_namespace( module, flatten =flatten)
    klastree.pprint_order_in_namespace( module)
    return klastree


if __name__=='__main__':

    s = """
p = int
class Record:
    Timestamp   = str
    ddd, ber, aaa = 2,3,4
    if 'NOT_FOR_ASSIGNMENT_ORDER':
        this = 5
    if 'qNOT_FOR_ASSIGNMENT_ORDER':
        that = 3
    class SubRec:
        a,c = 5,6
        b =    12
    d = SubRec
    ddd = 43    #repeat
    import os
    import compiler.ast
    import compiler.ast as xxxx
    from compiler.ast import Node
    class SubRec2:
        b = 5
    class ASubRec( SubRec, SubRec, SubRec2):
        z =    15
        b =    15
        def fun(x):
            z = 4
            return z

    class ASubRec2( ASubRec):
        o =   'oo'
"""

    help = """usage:
        no args       - print and test some internal source text
        name          - if endswith .py, loads file as module 'autoname'
                        else import name as module
        -module name  - force import name as module
    """

    import sys
    name = None
    is_module = False
    for a in sys.argv[1:]:
        if a == '-module':
            is_module = True
        elif a.startswith( '-'):
            print help
            sys.exit(-1)
        else:
            name = a
            if not name.lower().endswith( '.py'):
                is_module = True

    a = ASTVisitor4assign( do_function= True, do_import =True)
    if name:
        if is_module:  #module name
            print 'source - module:', name
            module = __import__( name )
            klastree = a.parseFile_of_module( module)
        else:
            print 'source - file (as module "autoname"):', name
            klastree = a.parseFile( name)   #source_file_name
            import imp
            f = open( name)
            try:
                module = imp.load_module( 'autoname', f, name, ('.py', 'r', imp.PY_SOURCE) )
            finally:
                f.close()
    else:
        print 'source - text:', s
        print '-----'
        klastree = a.parse( s)
    #klastree.pprint()

    if not name:
        exec s
        import __main__
        module = __main__

    klastree.set_order_in_namespace( module)    #,flatten=True to pre-calc flattened

    klastree.pprint_order_in_namespace( module)
    if not name:
        f = flatten_class__order( Record.ASubRec)
        print Record.ASubRec,f
        assert f == [ 'a','c','b', 'z','fun']
        f = flatten_class__order( Record.ASubRec2)
        assert f == [ 'a','c','b', 'z','fun', 'o']

if 0: #problem in exe mode
    def buildOrderClass( klas):
        from static_type.util.assignment_order import ASTVisitor4assign
        namespace = { klas.__name__  : klas }
        root = ASTVisitor4assign().parseClassSource( klas)
        root.set_order_in_namespace( namespace,
                    flatten= True,
                    ignore_missing_order= True,
                    with_classes= True)

            #print Calculation.parametri.aRow._order

# vim:ts=4:sw=4:expandtab
