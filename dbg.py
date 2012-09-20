#~2006 sdobrev
'various debug utilities: stack-level-counter, call-stack inspections'

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
    import inspect
    i
    frame = inspect.stack()[ level]# currentframe()
    frame = inspect.currentframe()
    try:
        localz = frame.f_back.f_locals
    finally:
        del frame
    if not name: return dict( localz)
    obj = localz[ name]
    return '%s=%s' % ( name, obj )


def dbg_func_framerec( i=0):
    import inspect
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

from threading import _Condition, currentThread
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
