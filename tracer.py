#sdobrev 2007
'trace+explain/log runtime python code - instrumentation of variables, methods'

#from dbg import dbg_funcname, dbg_func
from dictOrder import dictOrder
from attr import get_itemer
import operator, inspect

class OPdump( object):
    def __init__( me, name, func =None):
        me.name = name
        me.func = func
    def attach( me, owner):
        me.owner = owner
        return me
    def __call__( me, *args,**kargs):
        assert me.owner
        me.owner.prn( me.name, args, kargs)
    def methodcall( me, this, *args,**kargs):
        me.this = this
        me.owner = this.owner
        return me( *args, **kargs)

op_cmp = dict( gt='>', lt='<', ge='>=', le='<=', eq='==', ne='!=', )
op_arithm = dict( sub='-', add='+', mul='*', div ='/' )
op_arithm2 = dict( ('i'+k,v+'=') for k,v in op_arithm.items() )
op_arithm3 = dict( ('r'+k,v) for k,v in op_arithm.items() )
#TODO: radd rdiv etc decimal+var, int+var
opnames = {}
def f2op( d):
    d.update( ('__'+k+'__', v) for k,v in d.items() )   #gt -> __gt__
    opnames.update(d)
f2op( op_cmp)
f2op( op_arithm)
f2op( op_arithm2)
f2op( op_arithm3)

class OPbin( OPdump):
    '+,-,*,...'
    def __init__( me, name, func =None, reverse =False):
        me.name = name
        me.func = func
        me.reverse = reverse
    def __call__( me, o):
        owner = me.owner
        name = me.name
        this = me.this
        assert owner
        if name in op_cmp: owner.prn_( '?')
        args = me.reverse and (o,this) or (this,o)
        owner.prn_( args[0], opnames.get( name,name), args[-1])
        if isinstance( o, Var): o = o.value
        this = this.value
        args = me.reverse and (o,this) or (this,o)
        r = me.func( *args)
        owner.prn( '>>>result=', r )
        return r

class OPbin2( OPbin):
    '+=, -=, ...'
    def __call__( me, *args):
        r = OPbin.__call__( me, *args)
        me.this._value = r
        return me.this

def unvar2list( arg):   #recurse
    if isinstance( arg, (dict,dictOrder)):
        arg = arg.values()
    elif not isinstance( arg, (list,tuple,set)):
        if isinstance( arg, Var): return arg.value
        return arg
    return [ unvar2list(v) for v in arg ]

def unvar( arg):   #recurse
    if isinstance( arg, Var): arg = arg.value
    if isinstance( arg, dictOrder):
        return dictOrder( (k,unvar(v)) for k,v in arg.iteritems() )
    if isinstance( arg, dict):
        return dict( (k,unvar(v)) for k,v in arg.iteritems() )
    if isinstance( arg, (list,tuple,set)):
        return arg.__class__( unvar(v) for v in arg )
    return arg

class OPaggr( OPdump):
    def __call__( me, *args):   #,**kargs
        assert me.owner
        me.owner.prn_( me.name, args)    #kargs,
        args = unvar2list( args)
        r = me.func( *args)     #,**kargs)
        me.owner.prn( '>>>result=', r)
        return r

class Tracer( object):
    notrace = False
    tab = 4
    def __init__(me):
        me.lvl = 0
        me._nl = 1
    @property
    def indent(me): return me.lvl*me.tab*' '
    def prn( me, *args):
        me.prn_( *args)
        print
        me._nl = 1
    def prn_( me, *args):
        if me._nl: print me.indent,
        print ' '.join( str(s) for s in args if s is not ''),
        me._nl = 0
    def func( me, func, inargs =(), inkargs ={}):
        me._func = func
        f = getattr( func, 'orgfunc', func)
        #~~same as in call()
        method = getattr( f, 'im_func', None)
        args_direct = bool( method and f.im_self is not None)  #boundto:1, else:0
        fc = (method or f).func_code
        input_kargs = dict( zip( fc.co_varnames[ args_direct:args_direct+fc.co_argcount], inargs))
        input_kargs.update( inkargs)
        me._inputs = input_kargs

        what = method and f.im_self or f.__module__
        me.prn_( 'call', what, '.', f.__name__ )
        if not input_kargs: me.prn( '():' )
        else:
            i=me.tab*2
            me.prn( '(')
            me.prn( i*' ', (',\n'+me.indent+(i+2)*' ').join(
                    ['%s=%s' % kv for kv in input_kargs.iteritems() ]), '):' )
        me.lvl+=1

    def results( me, r):
        me._results = r
        me.prn( 'result:', r)
        me.lvl-=1
    def iterate( me, *args,**kargs):
        return OPdump( ':iterate').attach( me)( *args,**kargs)

    op_aggr  = 'min max sum'.split()
    ops_aggr = dict( (k, OPaggr( k, __builtins__[k])) for k in op_aggr )
    ops_bin = {}
    ops_bin.update( (k, OPbin( k,getattr( operator, k))) for k in op_arithm.keys()+op_cmp.keys() )
    ops_bin.update( ('__i'+k+'__', OPbin2( 'i'+k,getattr( operator, '__i'+k+'__'))) for k in op_arithm if k[0]!='_')
    ops_bin.update( ('__r'+k+'__', OPbin(  'r'+k,getattr( operator, k),reverse=True)) for k in op_arithm if k[0]!='_')
    traced = ops_aggr
    untraced = {}
    #seqs.update( ops_aggr)
    #seqs.update( ops_bin)

    def prepare( me, func):
        from func2code import Func_in_locals
        return Func_in_locals( func)
    class myFunc( object):
        __slots__ = 'fc owner'.split()
        def __init__( me, fc, owner =None):
            me.fc = fc
            me.owner = owner
        def __call__( me, *a,**k):
            if me.owner:    #processed func
                return me.owner.call( me.fc, a,k)
            return me.fc( *unvar(a), **unvar(k))
    def call( me, fc, args=(), kargs={}, args_direct =(), kargs_direct ={} ):
        dbg=0
        from func2code import Func_in_locals
        if not isinstance( fc, Func_in_locals):
            fc = me.prepare( fc)
        assert isinstance( fc, Func_in_locals)
        boundto = fc.boundto
        if boundto is not None: #bound method
            args_direct = [ boundto ] + list( args_direct)
        inputs = kargs.copy()
        inputs.update( zip( fc.arg_names[ len(args_direct):], args))
        me.func( fc, inkargs=inputs)
        vars = Vars()
        vars.owner = me
        if dbg: me.prn( 'call:arg_defaults', fc.arg_defaults)
        if dbg: me.prn( 'call:globals', fc.global_names)
        myglobs = {}
        globs = fc.orgfunc.func_globals
        for k in fc.global_names:
            if k in myglobs: continue
            if k in me.traced:
                if dbg: me.prn( 'call:attach', k)
                v = me.traced[k].attach(me)
            elif k in me.untraced:
                if dbg: me.prn( 'call:link', k)
                v = me.untraced[k]
            elif k in globs:
                v = globs[k]
                if callable(v):
                    if getattr( v, 'do_trace', False):
                        if dbg: me.prn( 'call:prepare', k)
                        v = me.myFunc( me.prepare( v), me)
                    elif inspect.isfunction(v) or inspect.ismethod(v):
                        if dbg: me.prn( 'call:unvar', k)
                        v = me.myFunc( v, None)
            else: #builtins
                continue
            myglobs[k]=v
        vars.setup_glocals( myglobs)
        vars.setup_glocals( zip(fc.arg_names, args_direct))
        vars.setup_glocals( kargs_direct)
        vars.update4Var( **inputs)  #XXX maybe skip prn() in this.. also try with default_value
        fc.locals = vars
        if dbg: print 44444444444, '\n  '.join( '%s=%s' % kv for kv in vars.iteritems())
        r = fc.call() #**dict( (k,vars._all[k]) for k in kargs))
        #r = fc.call_full( args_direct, kargs_direct) #**dict( (k,vars._all[k]) for k in kargs))
        me.results( r)
        return r

    def Var( me, k,v, notrace =False):
        owner = me
        if isinstance( v, dictOrder):
            r = dictOrder4Var()
            r.owner = owner
            r.copyfrom( v)
            if not notrace: owner.prn( 'assign', k, '=', r)
        else:
            r = Var( k,v, owner=owner, notrace=notrace)
        return r
    unvar = staticmethod( unvar)

class Var( object):
    __slots__ = 'name _value owner'.split()
    def __init__( me, name, value, owner =None, notrace =False):
        me.name = name
        me.owner = owner
        me.setval( value, notrace)
    def setval( me, v, notrace =False):
        if not notrace and not me.owner.notrace:
            me.owner.prn( 'assign', me.name, '=', v)
        if isinstance( v, Var): v = v._value
        me._value = v
    value = property( lambda me: me._value, setval)
    def __str__( me):
        return 'Var.%(me.name)s(=%(me.value)r)' % get_itemer(locals())
    __repr__ = __str__
    def __int__(me): return int( me.value)
    def __nonzero__(me): return bool(me.value)
    def __getattr__( me, k):
        if k in me.__slots__: return object.__getattr__( me,k)
        return getattr( me.value, k)

from new import instancemethod
for k in Tracer.ops_bin:
    if k.startswith('__'):
        op = Tracer.ops_bin[ k]
        setattr( Var, k, instancemethod( op.methodcall, None, Var) )

class Ref( object):
    __slots__ = ['ref']
    def __init__( me, ref): me.ref = ref
    def __str__( me): return 'Ref/'+str(me.ref)

class dictOrder4Var( dictOrder):
    'iterates like sequence of Var-Refs'
    def copy( me):
        r = me.__class__()
        r.owner = me.owner
        return r.copyfrom( me)
    def copyfrom( me, o):
        #me.owner.prn('copy')
        owner = me.owner
        notrace = False
        if owner and not owner.notrace: notrace = owner.notrace = True
        me.update( o)
        if notrace: del owner.notrace
        #owner.prn('copyok')
        return me
    def __iter__( me):
        lvl = me.owner.lvl
        for k,item in me.items():
            me.owner.lvl = lvl
            me.owner.iterate( item)
            me.owner.lvl+=1
            yield Ref(item)
        me.owner.lvl = lvl
    def __repr__( me): return 'dictOrder[ '+ repr( me.values())[1:]
    __str__ = __repr__
    #def __repr__( me): return str(me)
    def __getitem__( me, k):
        if isinstance( k,Var): k = k.name
        return dictOrder.__getitem__( me,k)
    def __setitem__( me, k, v):
        if isinstance( k,Var): k = k.name
        if isinstance( v, Ref): v = v.ref   #??? not needed so far
        if k in me:
            if isinstance( v, Var): v = v.value
            me[k].value = v
        else:
            dictOrder.__setitem__( me, k, Var( k,v, me.owner))

def refvariter( dic):
    for k,item in dic.items():
        assert isinstance( item, Var)
        me.owner.iterate( item)
        yield Ref(item)

class Vars( dict):
    owner = None
    def Var( me, k,v):
        return me.owner.Var( k,v)
        owner = me.owner
        if isinstance( v, dictOrder):
            r = dictOrder4Var()
            r.owner = owner
            r.copyfrom( v)
            owner.prn( 'assign', k, '=', r)
        else:
            r = Var( k,v, owner=owner)
        return r

    def __setitem__( me, k, v):
        #print 'setit', k, v
        if k not in me or isinstance( v, Ref):
            if isinstance( v, Ref): v = v.ref
            else: v = me.Var( k,v)
            dict.__setitem__( me, k, v)
        else:
            vv = me[k]
            if v is not vv: vv.value = v

    def setup_glocals( me, *args,**kargs):    #no Var-wrapping
        me.update( *args,**kargs)
    def update4Var( me, **kargs):       #Var-wrapping
        owner = me.owner
        if owner and not owner.notrace: notrace = owner.notrace = True
        for k,v in kargs.iteritems():
            me[k] = v
        if notrace: del owner.notrace

############################################
#decoratore
def trace_inside( func):
    'not tried, and no idea about classmethods/staticmethods'
    def explfunc( me, *a,**k):
        if me.EXPLAIN:
            return me.EXPLAIN.call( func, a,k, args_direct=(me,) )
        return func( me,*a,**k)
    explfunc.__name__ = func.__name__
    return explfunc
    #from tracer import Tracer
    #return Tracer.myFunc_in_locals( func)

def trace_outside( func):
    'works with plainmethods/classmethods/staticmethods'
    def explfunc( me, *a,**ka):
        f = func
        if isinstance( func, (staticmethod,classmethod)):
            f = func.__get__(me)
        else:
            f = instancemethod( func, me, me)
        if me.EXPLAIN:
            a =unvar(a)
            ka=unvar(ka)
            me.EXPLAIN.func( f, a,ka)
        r = f( *a,**ka)
        if me.EXPLAIN: me.EXPLAIN.results( r)
        return r
    f = isinstance( func, (staticmethod,classmethod)) and func.__get__(1) or func
    explfunc.__name__ = f.__name__
    return explfunc

# vim:ts=4:sw=4:expandtab
