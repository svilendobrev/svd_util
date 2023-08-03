#sdobrev 2008
'mix: logging destructor, valid weakref wrapper, Functor, mutex, neighbours-in-sequence ..'

class _DelLog:
    'hang to some object, so it will still be garbage-collected - while this one will not'
    def __init__(self,text,debug):
        self.text = text
        self._debug = debug
    def __del__(self):
        if self._debug.die: print( "==die", self.text)

def _w_ref_None(): return None
def w_ref( x):
    '''result() is always valid; using weakref.ref()
        as weakref.proxy is not 100% equivalent - e.g. wref(wref) does not work properly'''
    import weakref
    if x is None: return _w_ref_None
    return weakref.ref( x)

class Masker:
    'yield incrementally-shifted 1-bit mask, e.g. m=Masker(); print m(),m(),m() -> 1 2 4'
    def __init__( me): me.v = 1
    def __call__( me):
        r = me.v
        me.v <<= 1
        return r

##############
def neighbours( iter):
    'a,b,c,d -> a,b  b,c  c,d'
    #print 'neighbours', type(iter),list(iter)
    first = True
    for next in iter:
        if not first:
            yield prev,next
        prev = next
        first = False

##############

class Functor:
    _repr =str
    def __init__( me, func, *args, **kargs):
        me.func= func
        assert callable(func)
        me.args = args
        me.kargs = kargs
    def __call__( me, *args, **kargs):
        return me.func( *(args or me.args), **(kargs or me.kargs))
    def __str__( me):
        return '%s/%s( %s)' % (me.__class__.__name__, me.func,
                    str_args_kargs( _repr=me._repr, *me.args, **me.kargs) )

class Ptr:
    def __init__( me, obj): me.obj = obj
    def __str__( me): return str( me.obj )
    __repr__ = __str__

class Namer:
    """use as visible replacement of named constants
        WARNING: unless a dict-key, use .value to get the value!
    """
    def __init__( me, name, namespace =globals()):
        me.name = name
        me.value = namespace[ name]
    def __str__( me): return '%s(=%r)' % (me.name, me.value)
    def __hash__( me): return me.value

from enum import Enum
class strEnum( str, Enum):
    '''takes sequence of strings , or one string to be split by whitespace
    >>> s = strEnum( 'aname', ['a', 'bb', 'c'])
    >>> print( s, s.bb, s.bb.name)
    <enum 'aname'> aname.bb bb
    >>> t = strEnum( 'bname', 'a bb cc')
    >>> print( t, t.bb, t.cc.name)
    <enum 'bname'> bname.bb cc
    '''
    def _generate_next_value_(name, start, count, last_values): return name


#############

class Grab_stdout:
    def __init__( me):
        import sys, StringIO
        me._s = sys.stdout
        me.s = sys.stdout = StringIO.StringIO()
    grab = __init__
    def release( me):
        import sys
        sys.stdout = me._s
    def value( me): return me.s.getvalue()
    def __str__( me): return me.s.getvalue()

###############
#threading related

class UniqMutex:
    def __init__( me):
        me.all = {}
        import threading
        me._guard = threading.RLock()
        me.currentThread = threading.currentThread
        me.Thread = threading.Thread

    def attach( me, target):
        me._guard.acquire()
        try:
            if target in me.all: return True
            me.all[ target ] = Ptr( me.currentThread().getName() )
            return False
        finally: me._guard.release()

    def set( me, target, name):
        me._guard.acquire()
        try:
            me.all[ target] = name
        finally: me._guard.release()

    def detach( me, target):
        me._guard.acquire()
        try:
            try:
                del me.all[ target]
            except KeyError: pass
        finally: me._guard.release()

    def __str__( me):
        me._guard.acquire()
        try:
            return str( me.all)
        finally: me._guard.release()
    def __repr__( me):
        me._guard.acquire()
        try:
            return repr( me.all)
        finally: me._guard.release()

    def startTask( active_monitor, task_key, task_type, task, threaded =True, dbg_thread =False, *args,**kargs):
        """ registers and starts a task (in new thread or not), if no other
            task of same task_type is registered. un-registers at end, at any rate.
            appends task_type to thread's name.
        """
        if threaded:
            if active_monitor.attach( task_key):
                print( '! another', task_type, 'is running:', active_monitor)
                return
            def doer():
                try:
                    task( *args, **kargs)
                finally:
                    active_monitor.detach( task_key)
                    if dbg_thread: print( name, 'Ended')
            thr = active_monitor.Thread( target= doer )
            name = '%s:%s' % ( thr.getName(), task_type)
            thr.setName( name)
            active_monitor.set( task_key, name)
            thr.start()
            if dbg_thread: print( name, 'Started')
        else:
            task( *args, **kargs)


class mutexPtr: #not really working reasonable
    def __init__( me, obj):
        me.obj = obj
        import threading
        me._guard = threading.RLock()
    def get( me):
        me._guard.acquire()
        return me.obj
    def release( me):
        me._guard.release()


class TreeByRelationAttr( object):
    def __init__( me, items, relation_attr, key_func =None):
        from kjbuckets import kjGraph
        me.key_func = key_func or (lambda o: o)
        d = {}
        for item in items:
            p = getattr(item, relation_attr)
            d.setdefault(p,[]).append(item)
        lst = []
        for k, v in d.iteritems():
            lst.extend( [(k, item) for item in v] )

        me.kjdict = {}
        kjlist = []
        for i,j in lst:
            keys = [ me.key_func( o) for o in (i,j) ]
            me.kjdict.update( zip( keys, (i,j)))
            kjlist.append( keys)
        me.graph = kjGraph( kjlist)

    def children( me, item):
        return [ me.kjdict[i] for i in me.graph.neighbors( me.key_func(item)) ]

    def walk_depth_first( me, item, with_root=False):
        res = []
        if with_root: res.append( item)
        for c in me.children( item):
            res += me.walk_depth( c)
        return res


if __name__ == '__main__':
    def test():
        '''
        >>> list( neighbours( 'abcd') )
        [('a', 'b'), ('b', 'c'), ('c', 'd')]
        >>> list( neighbours( 'abc') )
        [('a', 'b'), ('b', 'c')]
        >>> list( neighbours( 'ab') )
        [('a', 'b')]
        >>> list( neighbours( 'a') )
        []
        >>> list( neighbours( '') )
        []
        '''
        pass

    import doctest
    doctest.testmod()

# vim:ts=4:sw=4:expandtab
