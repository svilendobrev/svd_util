#~2006 sdobrev
'various debug utilities: stack-level-counter, call-stack inspections'
from __future__ import print_function
import inspect

class Level:
    '''stack-frame-living recursion-depth level counter. use as:
     somefunc()...
        if _debug: l=level(); print l, 'something'
        if _debug: print l, 'another:'
        somefunc()...
    '''
    def __init__( me, tab ='  ', initial =1):
        me.a = max( initial -1, -1)
        me.tab = tab
    def __str__( me):  return me.a * me.tab
    def __call__( me):
        return Level._level( me)
    class _level:
        def __init__( me, leveler):
            me.leveler = leveler
            leveler.a +=1
        def __del__( me):  me.leveler.a -=1
        def __str__( me):  return str( me.leveler)

def dbg_value( name, level =0):
#    frame = inspect.stack()[ level]# currentframe()
    frame = inspect.currentframe()
    try:
        localz = frame.f_back.f_locals
    finally:
        del frame
    if not name: return dict( localz)
    obj = localz[ name]
    return '%s=%s' % ( name, obj )

def dbg_value_g( name, level =0):
    frame = inspect.stack()[ level][0]
    try:
        localz = frame.f_locals
        if name not in localz: localz = frame.f_globals
    finally:
        del frame
    return localz[ name]


def dbg_func_framerec( i=0):
    'framerec: frame object, filename, line number, function name, list of lines of context source code, index of current line within that list)'
    return inspect.stack()[i] #[0].f_code

def dbg_funcname_locals( i=0):
    f1,f2 = dbg_func_framerec( slice( i+1, i+3))
    return ( f2[ 3], f1[0].f_back.f_locals )

def dbg_funcname( i=2, with_filename =False):
    import traceback
    filename, linenumber, functionname, text = traceback.extract_stack()[-i]
    if with_filename: return functionname, filename
    return functionname

def dbg_funcstack( start=2, depth=3, dlm=''):
    import traceback
    return dlm.join( traceback.format_list( traceback.extract_stack( limit=start+depth+1)[-start-depth+1:-start+1] ))
    #traceback.print_list( traceback.extract_stack( )[-start-depth+1:-start+1] )


#these not really belong here
def getdefaultargs( func):
    a = inspect.getargspec( func)
    return dict( zip( reversed( a.args), reversed( a.defaults or ())))
def getdefaultargs_wrap( func):
    if isinstance( getattr( func, 'me', None), dbg.funcwrap):
        func = func.me.func
    return getdefaultargs( func)
def func_meta( func):
    '.module, .args, .argdefaults=dict; .varkargs, .varargs'
    func = getattr( func, '__func__', func)
#            print( 3333333, ffunc, dir(ffunc))
    #if isinstance( func, classmethod): ffunc = func.__func__
    a = inspect.getargspec( func)
    func.args = a.args
    func.varkargs = a.keywords
    func.varargs  = a.varargs
    #func.argdefaults = getdefaultargs( func)
    func.argdefaults = dict( zip( reversed( a.args), reversed( a.defaults or ())))
    func.module = func.func_globals.get( '__name__')
    if func.module == '__main__':
        func.module = func.func_globals.get( '__file__')
    return func
###


class log_funcname:
    'set .do_log, use .log() in some func'
    do_log = True
    @classmethod
    def log( me, msg =None, no_locals =False ):
        if not me.do_log: return
        if msg: print( msg, end= ' ')
        if no_locals:
            print( dbg_funcname( 1+2), '(..)')
        else:
            print( *dbg_funcname_locals( 1))

class funcwrap:
    ''' do-nothing and/or log; e.g.
        rename = funcwrap( os.rename)
        ..
        rename( a,b) would log it but not exec (if log=True, really=False)
        '''
    really = True
    log = True
    pfx = ''
    def __init__( me, func): me.func = func
    def __call__( me, *a, **k):
        if me.log: print( me.pfx+me.func.__name__, a, k)
        if me.really: return me.func( *a, **k)
    def methodwrap( me):
        'use as funcwrap( method).methodwrap()'
        def call( *a,**k): return me( *a,**k)
        call.__name__ = '@'+me.func.__name__
        call.me = me
        return call


class log_pseudo:
    ''' l = Log()
    l.mymethod( args)
    l.anotherfunc( 1, a=2, b=3)
    '''
    def __getattr__( me, a):
        print( ' >', a, end=' ')
        return print
#       print ' >', ' '.join(str(x) for x in a)

class namewrap:
    ''' do-nothing and/or log; e.g.
        rename = funcwrap( os.rename)
        ..
        rename( a,b) would log it but not exec (if log=True, really=False)
        '''
    really = True
    log = True
    def __init__( me, namespace): me.namespace = namespace
    def __getattr__( me, a):
        if me.really:
            r = funcwrap( me.namespace[a])
            r.log = me.log
            r.really = me.really
            return r
        if me.log:
            print( ' >', a, end=' ')
            return print
        return lambda *a,**k: None

import types as _types

class Meta4log( type):
    '''use as __metaclass__ and setup these, per-class (auto-aggregated along inheritance):
    LOG_PFXS      = seq of prefixes of methods to log; empty->None; *->all
    LOG_PFXS_EXCL = seq of prefixes of methods to not log; empty->None; *->all
    '''
    funcwrap = funcwrap     #inherit+overwrite to set local .really/.log
    def __new__( meta, name, bases, dict_):
        def pfxs( name):
            log_pfxs = dict_.get( name,())
            log_pfxs = set( isinstance( log_pfxs, basestring) and log_pfxs.split() or log_pfxs )
            for b in bases:
                log_pfxs.update( getattr( b, name, ()))
            dict_[ name ] = log_pfxs
            return log_pfxs
        log_incl = pfxs( 'LOG_PFXS')
        log_excl = pfxs( 'LOG_PFXS_EXCL' )
        #print( 1111111, name, log_incl, log_excl )
        def is_pfx( name):
            if '*' in log_excl: return
            for p in log_incl:
                if p=='*' or name.startswith( p):
                    for ex in log_excl:
                        if name.startswith( ex): return
                    return True
        dict_.update( (k, meta.funcwrap( v).methodwrap())
                for k,v in dict_.items()
                if isinstance( v, ( _types.FunctionType, _types.GeneratorType, _types.MethodType, )) and is_pfx( k)
                )
        return type.__new__( meta, name, bases, dict_)

try:
    from threading import _Condition
except (ImportError, NameError):   #py3.3+
    from threading import Condition as _Condition
from threading import currentThread

def dbg_funcname_thread( i=3):
    #thread
    return '%s | %s() ' % (currentThread().getName(), dbg_funcname(i+1) )


class Condition( _Condition):
    name = ''
    def __init__( me, *a,**k):
        _Condition.__init__( me, *a,**k)
        me.__acquire = me.acquire
        me.acquire = me.my_acquire
        me.__release = me.release
        me.release = me.my_release
        import sys
        me.stderr = sys.stderr
    def __str__( me):
        return 'cond '+me.name  #%s/%d' % (me.name, id(me))
    def z_note( me, format, *args):
        if 1:#me.__verbose:
            dlm = ' > '
            me.stderr.write( dlm)
            _Condition._note( me, format,*args)
            me.stderr.write( dlm + dbg_funcstack( start=4,depth=3, dlm=dlm) + '\n' )
    def my_acquire( me, *a,**k):
        me.stderr.write( '%s: %s acquiring...\n' % ( dbg_funcname_thread(), me) )
        me.__acquire( *a,**k)
        me.stderr.write( '%s: %s acquired\n' % ( dbg_funcname_thread(), me) )
    def znotifyAll( me, *a,**k):
        me.stderr.write( '%s: %s notifyAll\n' % ( dbg_funcname_thread(), me) )
        return _Condition.notifyAll( me, *a,**k)
    def my_release( me, *a,**k):
        me.stderr.write( '%s: %s release\n' % ( dbg_funcname_thread(), me) )
        return me.__release( *a,**k)
    def wait( me, *a,**k):
        me.stderr.write( '%s: %s waiting\n' % ( dbg_funcname_thread(), me) )
        _Condition.wait( me, *a,**k)
        me.stderr.write( '%s: %s eo wait\n' % ( dbg_funcname_thread(), me) )

    def busy_handler4sqlite( me, data, tablename, num_busy ):
        thr = currentThread().getName()
        print( "__busy_handler, %s: table/index %r (num_busy %d)" % (thr, tablename, num_busy))
        me.acquire()
        me.wait()
        me.release()
        return True


if __name__=='__main__':
    a = 2
    print( dbg_value( 'a' ))
    def xfunc():
        print( dbg_funcname(2))
        print( dbg_funcstack())
    def yfunc():
        print( dbg_funcname())
        print( dbg_funcstack())
        xfunc()
    yfunc()

# vim:ts=4:sw=4:expandtab
