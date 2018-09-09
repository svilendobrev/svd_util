# sdobrev 2008-9
'inspect variables used in function, local/global - for tracing/explain'

from ext.byteplay import Code, opmap

replacer = {
    opmap['LOAD_FAST']:   opmap['LOAD_NAME'],
    opmap['LOAD_DEREF']:  opmap['LOAD_NAME'],
    opmap['STORE_FAST']:  opmap['STORE_NAME'],
    opmap['STORE_DEREF']: opmap['STORE_NAME'],
}
opload_glob = opmap['LOAD_GLOBAL']

def get_var_attr_usage( code, root_var, subattrs =()):
    x=0
    for c,arg in code.code:
        if c in [opmap['LOAD_FAST'], opmap['LOAD_NAME']]:
            if arg == root_var:
                x=1
                #print 111111, c,arg
                continue
        if not x or c != opmap['LOAD_ATTR']: continue
        if x == 1+len(subattrs):
            yield arg
        elif arg == subattrs[x-1]:
            x += 1
            #print 222222, c,arg
            continue
        x=0
def get_attr_usage( func, attrpath ):
    ''' attrpath = [a, b, c] -> a.b.c
        attrpath = [1, b.c] -> func_args[1].b.c
    '''
    if not isinstance( func, Code):
        code = Code.from_code( getattr( func, 'im_func', func).func_code)
    else: code = func
    #print code.code
    root_var = attrpath[0]
    subattrs = attrpath[1:]
    if isinstance( root_var, int):  #argix
        root_var = code.args[ root_var]
    return get_var_attr_usage( code, root_var, subattrs)
#usage: print list( get_attr_usage( myfunc, 1, ['algo'] ))

def execode( func, noargs =True, get_all_data =False):
    '''expose func code as plain executable block without own namespace
    usage: pass all args/vars in locals/globals:
        cf = execode( func1)
        #no return value:
        exec cf in mylocalz( x=7, y=6, max= mymax )
        #with return value:
        r = eval( cf, mylocalz( x=9, y=0, max= mymax ) )

    ref: http://wiki.python.org/moin/ByteplayDoc
        http://www.voidspace.org.uk/python/articles/code_blocks.shtml
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/498242
    '''

    fc = getattr( func, 'im_func', func).func_code
    code = Code.from_code( fc)
    #XXX TODO:
    #   LOAD_DEREF -> LOAD_NAME: needs same to be done in all nested funcs!!
    #if opmap['LOAD_DEREF'] in [ c for c,a in code.code ]:
    #    print code.code
    #print code.code
    #print code.__dict__
    assert not code.varargs, func
    assert not code.varkwargs, func
    code.code = [ (replacer.get( opcode,opcode),arg) for opcode,arg in code.code]
    global_names = [ arg for opcode,arg in code.code if opcode == opload_glob ]
    code.newlocals = False  #no local namespace
    assert not code.freevars
    code.freevars = ()      #kill (to-be-bound) vars
    org_args = code.args
    if noargs:
        code.args = ()      #kill (to-be-bound) args
    c = code.to_code()
    #assert not fc.co_cellvars, fc.co_cellvars
    if not get_all_data: return c
    return c, org_args, global_names
    return dict( code=c, org_args=org_args, global_names=global_names)

#for a in 'varnames cellvars freevars names'.split():
#    print getattr(c,'co_'+a)

class Func_in_locals:
    '''calling a func within externaly provided locals(); *args,*kargs not allowed
    fc = Func_in_locals( f1)
    fc.locals = dlocalz( max=mymax)
    print fc( x=4, y=0)
    fc.locals = dlocalz( max=anothermax)
    print fc( 3)
'''
    #ahhh... this setup of arguments.. see expr.makeExpresion()
    def __init__( me, func, glocalsdict =None):
        me.orgfunc = func
        method = getattr( func, 'im_func', None)
        me.ismethod = bool( method)
        func = method or func
        me.func = func
        me.locals = glocalsdict
        me.code, me.arg_names, me.global_names = execode( func, get_all_data=True)
        #import inspect
        #args,vargs,kwargs,defaults = inspect.getargspec(functor)
        #if inspect.ismethod( functor): args = args[1:]
        #assert not vargs
        #assert not kwargs
        defaults = func.func_defaults or ()
            #end-aligned: arg[-1] -> defaults[-1], ...
        me.arg_defaults = dict( (me.arg_names[-1-i], defaults[ -1-i]) for i in range(len(defaults)) )
    @property
    def boundto( me):
        if me.ismethod: return me.orgfunc.im_self
        return None

    def call_full( me, args, kargs):
        allargs = {}
        allargs.update( me.arg_defaults)

        assert len( args) <= len( me.arg_names), 'more pos.args'
        argvs = dict( zip( me.arg_names, args) )
        allargs.update( argvs)

        dups = set(kargs) & set(argvs)
        assert not dups, 'duplicate args: %(dups)s' % locals()
        allargs.update( kargs)

        allnames = set(allargs)
        expnames = set(me.arg_names)
        assert allnames == expnames, (len(allnames) < len(expnames) and 'not enough args' or 'more args') + ': given %(allnames)s, expect %(expnames)s' % locals()
        me.locals.update( allargs)

        return eval( me.code, {}, me.locals)

    __call__ = call_full

    def call( me):
        'use whatever is in me.locals + defaults '
        me.locals.update( (k,v) for k,v in me.arg_defaults.iteritems() if k not in me.locals)
        return eval( me.code, me.locals)

if __name__ == '__main__':

    def f1(x,y):
        a = max( x,3)
        if y: return 5
        return a

    def f2(x,y):
        pass

    class dlocalz( dict):
        def __setitem__( me,k,v):
            print 'seti', k,v
            dict.__setitem__( me,k,v)

    def mymax( *az):
        print 'mymax', az
        return az[-1]

    cf = execode( f1)
    exec cf in dlocalz( x=7, y=6, max= mymax )
    #no return value!

    r = eval( cf, dlocalz( x=9, y=0, max= mymax ) )
    print r

    print '-----------'
    fc = Func_in_locals( f1)
    fc.locals = dlocalz( max=mymax)
    print fc( x=4, y=0)
    print fc( 3,2)
    #print fc( 3)       #less args
    #print fc( y=2)     #less args
    #print fc( 5,x=2,)  #dup
    #print fc( 5,2,4)   #more args
    #print fc( 5,2,t=4) #more args
    if 0:
        print '-----------'
        # these below do not work well
        f2.func_code = execode( f1, )#noargs=False)
        x=5;y=2; max=mymax
        print f2()# x=8, y=1)   #

        print eval( f2.func_code, dlocalz( x=9, y=0, max= mymax ) )# x=8, y=1)

        def z( x=3,y=0):
            max=lambda *a: a[0]
            print f2()# x=8, y=1)
        z()

# vim:ts=4:sw=4:expandtab
