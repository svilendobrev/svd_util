#sdobrev 2006
'expression-tree builder and visitor/evaluator'

import operator

class _Expr( object):
    __slots__ = ()

    def __and__( me, o): return Expr( 'and', me,o)
    def __or__(  me, o): return Expr( 'or',  me,o)
    def __xor__( me, o): return Expr( 'xor', me,o)
    def __invert__( me): return Expr( 'not', me)

    def __gt__( me, o): return Expr( 'gt', me,o)
    def __lt__( me, o): return Expr( 'lt', me,o)
    def __le__( me, o): return Expr( 'le', me,o)
    def __ge__( me, o): return Expr( 'ge', me,o)
    def __eq__( me, o): return Expr( 'eq', me,o)
    def __ne__( me, o): return Expr( 'ne', me,o)

    def __add__( me, o): return Expr( '+', me,o)
    def __sub__( me, o): return Expr( '-', me,o)
    def __mul__( me, o): return Expr( '*', me,o)
    def __div__( me, o): return Expr( '/', me,o)
    def __mod__( me, o): return Expr( '%', me,o)

    #'r'versions are reverse - if a.op(b) doesnot work, b.rop(a) is tried
    def __rand__( me, o): return Expr( 'and', me,o)
    def __ror__(  me, o): return Expr( 'or',  me,o)
    def __rxor__( me, o): return Expr( 'xor', me,o)
    def __radd__( me, o): return Expr( '+', o,me)
    def __rsub__( me, o): return Expr( '-', o,me)
    def __rmul__( me, o): return Expr( '*', o,me)
    def __rdiv__( me, o): return Expr( '/', o,me)
    def __rmod__( me, o): return Expr( '%', o,me)
    '''more:
__r/divmod__
__r/floordiv__
__r/lshift__
__r/pow__
__r/rshift__
__r/truediv__
'''



class Expr( _Expr):
    class Visitor: pass
    __slots__ = ( 'op', 'args', 'kargs', 'arg_names', 'arg_defaults' )
    def __new__( klas, op ='pic-kle', *args, **kargs):
        ''' op no args === const
            empty op === const in arg1
            op == 'var': variable
            op == 'pic-kle': just for pickling -> __new__() + setattr
        '''
        if op != 'pic-kle':
            if not args:
                args = (op,)
                op = ''
            if not op:
                assert len(args) == 1
                return Const( args[0] )
        return object.__new__( klas, op, *args, **kargs)

    def __init__( me, op, *args, **kargs):
        assert op
        assert args
        #assert len(args) <= 2
        me.op = op
        me.args = args
        me.kargs = kargs

    def _arg( me, a, visitor, level=0, stack =()):
        if isinstance( a, Var):
            r = visitor.var( a._name___)
        elif isinstance( a, _Expr):
            r = a.walk( visitor, level=level, stack=stack)
        elif isinstance( a, (list,tuple)):
            r = type(a)( me._arg( x, visitor, level, stack) for x in a)
        else:
            r = visitor.const( a)
        return r

    def walk( me, visitor, level=0, stack=()):
        args = me.args
        kargs = me.kargs
        op = me.op
        stack = stack+(me,)
        bargs = []
        for a in args:
            r = me._arg( a, visitor, level+1, stack= stack )
            bargs.append( r)
#        print level, op, visitor
        return visitor( level, op, stack=stack, *bargs, **kargs)

    pfx = 0     #set to 1 for hierarchical str()
    tab = '   '
    def __str__( me):
        args = me.args
        op = me.op
        assert op
        assert args
        r = op
        r+= '( '
        if Expr.pfx:
            pfx = (Expr.pfx -1) * Expr.tab
            pfx2 = '\n'+pfx + Expr.tab
            Expr.pfx +=1
            r += ','.join( pfx2+repr(s) for s in args )
            Expr.pfx -=1
            r += '\n'+pfx+')'
        else:
            r += ', '.join( repr(s) for s in args ) + ' )'
        return r
    __repr__ = __str__

class Function( Expr):
    def __init__( me, op, is_method =False, *args, **kargs):
        Expr.__init__( me, (is_method and 'M-' or 'F-') + op, *args, **kargs)


class Const( _Expr):
    __slots__ = [ 'value' ]
    def __init__( me, value):
        assert isinstance( value, (int, float, long, str) )
        me.value = value
    def walk( me, visitor, level ='ignored', stack ='ignored'):
        return visitor.const( me.value )
    def __str__( me):
        return repr( me.value )
    __repr__ = __str__


class Var( _Expr):
    '''don't expose ANY easily-used plain atributes, e.g. .name, .walk;
    hence .walk and _Expr.walk go expanded in Expr.walk'''
    __slots__ = [ '_name___' ]
    def __init__( me, name):
        assert isinstance( name, str), `name`
        assert name
        me._name___ = name
    def __getattr__( me, k):
        return Var( me._name___+'.'+k)
    def __str__( me):
        return 'var:'+me._name___
    __repr__ = __str__
    def __call__( me, *args, **kargs):      #func/method
        name = me._name___
        dots = name.count('.')
        assert dots >=1
        if dots < 2: #a(..) or a.b(..)
            is_method = False
        else:
            varname, funcname = name.rsplit('.',1)
            args = [ Var( varname) ] + list( args )
            name = funcname
            is_method = True
        return Function( name, is_method, *args, **kargs)

class Subclass( _Expr):
    '''
    eval1:    isinstance( x, B1)  #C,D,F
    eval2:    return x.__class__ in ( B1,C,D,F)
    sql/non-odbms:   "Xtable.__class__ in ( 'B1','C','D','F')"
    '''
    __slots__ = [ 'varname', 'typ' ]
    def __init__( me, var, typ):
        assert isinstance( var, Var)
        from types import ClassType
        assert isinstance( typ, (type, ClassType))
        me.varname = var._name___
        me.typ = typ
    def walk( me, visitor, level ='ignored', stack ='ignored'):
        return visitor.subclass( me.varname, me.typ )
    def __str__( me):
        return 'subclass( ' + me.varname + ', ' + str(me.typ) + ' )'



############# interpreters

class as_text_expr( Expr.Visitor):
    def var( me, name): return 'var:'+name
    def subclass( me, name, typ):
        return ' '.join( [ 'issubclass(', name, ',', typ.__name__, ')' ] )
    def const( me, value): return repr( value)
    def __call__( me, level, op, *args, **kargs_ignore):
        is_func = op.startswith('F-')
        is_method = op.startswith('M-')
        if is_func or is_method:
            op = op[2:]
        else:
            op = {'gt':'>', 'lt':'<', 'ge':'>=', 'le':'<=', 'eq':'==', 'ne':'!=', }.get(op,op)
        if is_method:
            r = args[0] + '.' + op + '( ' + ', '.join(args[1:]) + ' )'
        elif len(args)==1 or is_func:
            r = op + '( ' + ', '.join( str(x) for x in args) + ' )'
        else:
            assert len(args)==2
            r = ' '.join( [ '(', args[0], op, args[1], ')' ] )
        return r

as_expr = as_text_expr()


class as_text_sql( Expr.Visitor):
    '''expects typ.subclasses to contain (pre-generated) all
    subtypes of typ (of interest)'''
    def subclass( me, name, typ):
        return ' '.join(
            ['(', name.upper()+'.__class__', 'in (',
                ', '.join(
                    repr( isinstance( t, str) and t or t.__name__)
                        for t in getattr( typ, 'subclasses',
                            ['code-generated-names-of-all-subclasses-of-',  typ.__name__ ] )
                    ),
             ')' ] )
    def var( me, name): return 'var:'+name.upper()
    def const( me, value): return repr( value)
    def __call__( me, level, op, *args, **kargs_ignore):
        op = {'gt':'>', 'lt':'<', 'ge':'>=', 'le':'<=', 'eq':'=', 'ne':'<>',
                'xor':'<>', }.get(op,op)
        if len(args)==1:
            r = ' '.join( [ op, '(', args[0], ')' ] )
        else:
            r = ' '.join( [ '(', args[0], op, args[1], ')' ] )
        return r
as_sql = as_text_sql()


class Eval( Expr.Visitor):
    def __init__( me, context):
        me.context = context
    def var( me, name): return me.context[ name ]

    def subclass1( me, name, typ):
        return isinstance( me.context[ name ], typ )

    '''expects typ.subclasses to contain (pre-generated) all
    subtypes of typ (of interest)'''
    def subclass2( me, name, typ):
        try:
            subclasses = typ.subclasses
        except AttributeError, e:
            print e.__class__.__name__, e
            print ' !!expects .subclasses to contain all subclasses of interest'
            subclasses = ()
            #e.args = (e.args[0]+'\nexpects .subclasses to contain all subclasses of interest' ,)
            #raise
        c = me.context[ name ].__class__
        return c == typ or c in subclasses

    subclass = subclass1

    def const( me, value): return value

#    def function(me, funcname, *args): return funcname+str(args) # ????

    arithm_op = {
            'gt': None,
            'lt': None,
            'ge': None,
            'le': None,
            'eq': None,
            'ne': None,
            '+' : '__add__',
            '-' : '__sub__',
            '*' : '__mul__',
            '/' : '__div__',
            '%' : '__mod__',
        }
    bool_op = { 'or': 'or_',
                'xor': None,
                'and': 'and_',
                'not': 'not_',
            }
    def __call__( me, level, op, *args, **kargs_ignore):
        #print 'evalcal', level, op, args
        if op in me.arithm_op:
            return getattr( operator, me.arithm_op[op] or op ) ( *args)
        if op in me.bool_op:
            return getattr( operator, me.bool_op[op] or op) ( *(bool(a) for a in args))

        if op.startswith( 'M-'):
            return getattr( args[0], op[2:])( *args[1:] )
        if op.startswith( 'F-'):
            op = op[2:]
            f,funcname = op.split('.')
            return getattr( me.context[ f], funcname)( *args)

        if op in [ 'like', 'between', 'in_', 'max', 'endswith' ]:
            return None #op

        assert 0, (op, args)

_dict = {}
def makeExpresion( functor):
    'converts plain python function into Expr'
    import inspect
    args,vargs,kwargs,defaults = inspect.getargspec(functor)
    if inspect.ismethod( functor): args = args[1:]
    assert not vargs
    assert not kwargs
    #assert not defaults
    newargs = dict( (k,Var(k)) for k in args )
    r = functor( **newargs)
    r.arg_names = args
    if defaults:            #end-alignment: arg[-1] -> defaults[-1], ...
        arg_defaults = dict( (args[-1-i], defaults[ -1-i]) for i in range(len(defaults)) )
    else: arg_defaults = _dict
    r.arg_defaults = arg_defaults
    return r


###################

class GluerOP( object):
    '''Glue similar function-filters together via some operator &,|,..
       resultfunc = GluerXX( *funcs).__call__
    '''
    op = None
    def __init__( me, *selects):
        me.selects = [ s for s in selects if s is not None]
    def __call__( me, self):
        r = None
        for s in me.selects:
            s = s( self)
            if r is None: r = s
            else: r = me.op( r, s)
        assert r is not None
        return r

class GluerAnd( GluerOP):
    op = operator.__and__
class GluerOR( GluerOP):
    op = operator.__or__



if __name__ == '__main__':
    if 10:
        a = Var('a')
        print a
        print Expr(1)
        b = Var('b')
        c = Expr('c')
        d = Var('d')
        n5 = Expr(5)

        print 1
        z = a or b and c
        print z
        print 2
        print (a>1)
        p = (1 > a) | (b ==2)
        print p
        p = (a>0) & ~ (c == 'aa')
        print p
        p = (d > n5)
        print p
        p = (a>3) ^ p
        print p

    ##### hierarchical print
        Expr.pfx = 1
        print p
        Expr.pfx = 0

        print 'expr:'
        print p.walk( as_expr)
    ######
        print 'eval:'
        ev = Eval( dict( a=4, d=7, ) )
        print ev.context
        print p.walk( ev)
    ######
        print 'sql:', p.walk( as_sql)

    ######
        def f(a,c):
            return (a >3) | (c >1)
        print 'functor:', makeExpresion(f).walk(as_expr)

####
    class B1: pass
    class B2(B1): pass
    s = Subclass( a, B1)
    print s
    print 'expr:', s.walk( as_expr)

    ev.context['a'] = B2()
    print 'eval:', s.walk( ev)

    B1.subclasses = [f.__name__ for f in (B1,B2)]

    print 'sql:', s.walk( as_sql)

######
    def f(d,x):
        return Subclass( x, B1) & (x.a >3) | (d !=1)
    e = makeExpresion(f)
    print 'functor:', e
    print '/expr:', e.walk( as_expr)
    print '/sql :', e.walk( as_sql)
######

    class ListChk:
        def in_( me, val, lst):
            #print 'chk', val, lst,
            r = val in lst
            #print r
            return r

    class Test:
        from engine.testbase import Case    #XXX TODO FIXME
        VERBOSE = 1

        class A:
            def __init__( me, a, b, c, d):
                me.a, me.b, me.c, me.d = ( a, b, c, d)
                me.ex = ListChk()
            def __str__( me): return 'A(a:%s b:%s c:%s d:%s)' % (me.a, me.b, me.c, me.d)
            __repr__ = __str__
            def __eq__( me, other):
                same = me.__class__ is other.__class__
                if not same: return same
                empty=1
                for k,v in me.__dict__.iteritems():
                    empty=0
                    ov = getattr( other, k, None)
                    if not (ov == v):
                        return False
                if empty:
                    for k,v in other.__dict__.iteritems():
                        if v is not None:
                            return False        #not empty -> not same
                    #not entered -> empty -> same
                return True
            def __ne__( me, o): return not me.__eq__( o)

        class Sample:
            def __init__( me, expr, expectedVal, name =''):
                me.expr = expr
                me.expected = expectedVal
                me.name = name
            def testData( me): return '\nEXPR: ' + str( me.expr)
            def testResult( me, res): return '''
RESULT:%s
EXPECTED:%s
''' % (res, me.expected)
            def __str__( me): return str( me.expr)

        class EvalTest( Case):
            def __init__( me): Test.Case.__init__( me, me.__class__.__name__, [], [])
            def setup( me):
                Test.Case.setup( me)
                A = Test.A
                w = A( 3, 5, 1, 7)
                v = A( 1, 2, 3, 4)
                u = A( 4, 6, 1, 8)
                t = A( 7, 0, 0, 3)
                x = A( 8, 1, 7, 0)
                y = A( 9, 6, 8, 1)
                z = A( 3, 5, 3, 9)
                me.initialState = [w, v, u, t, x, y, z]
                a = Var( 'a')
                b = Var( 'b')
                c = Var( 'c')
                d = Var( 'd')
                ex= Var( 'ex')
                t_ = Test.Sample
                me.testSamples = [
                    t_( (a>3),   [u,t,x,y],      'Gt'),
                    t_( (a<3),   [v],            'Lt'),
                    t_( (a<=4),  [w,v,u,z],      'Le'),
                    t_( (a>=4),  [u,t,x,y],      'Ge'),
                    t_( (b==6),  [u,y],          'Eq'),
                    t_( (d!=3),  [w,v,u,x,y,z],  'Ne'),
                    t_( ((a>3) & (b==6)),   [u,y],      'And'),
                    t_( ((a<3) | (b==6)),   [v,u,y],    'Or'),
                    t_( ((a<=4) ^ (b==6)),  [w,v,y,z],  'Xor'),
                    t_( (~(a>3)),           [w,v,z],    'Not'),
                    t_( ((a>3) | (b==5) & (c==1) ^ (d<8)),    [v,u,t,x,y],      'more complex expr1'),
                    t_( ((a>2) & ~(b==5)),                    [u,t,x,y],        'more complex expr2'),
                    t_( ((a>2) & ((b==5) ^ (c==1)) | (d<8)),  [w,v,u,t,x,y,z],  'more complex expr3'),
                    t_( ((a>=2) & ((b!=6) | (c==1)) | (d>8)), [w,u,t,x,z],      'more complex expr4'),
                    t_( ((a>2) | ((b==5) | (c==1)) | (d ^ 8)), [w,u,t,x,y,z],   'more complex expr5'),
                    t_( (d ^ 8), [x], 'var xor const'), ## can mean different things now: xor( bool(d), bool(8))
                    t_( ([a,b>2]==c),    [], 'list of expr'),
                    t_( ex.in_( 0*a+3, [a,b+2]),    [w,x,z], 'func of list of expr'),
                ]
            def testEach( me, testSample):
                'tests evaluation'
                return list( i for i in me.initialState
                        if testSample.expr.walk( Eval( i.__dict__)))
        class WalkTest( EvalTest):
            'tests walker'
            def testEach( me, testSample):
                def simple_visitor( you): pass # TODO XXX
                testSample.expr.walk( simple_visitor)
    #    makeExpr
    #    class ConstTest( EvalTest):
    #    class SubclassTest( EvalTest):

    from engine.testutils import testMain
    testMain( [
    #    Test.WalkTest(),
    #    Test.ConstTest(),
        Test.EvalTest(),
    #    Test.MakexTest(),
    #    Test.SubclassTest(),
        ], verbosity= Test.VERBOSE )

# vim:ts=4:sw=4:expandtab
