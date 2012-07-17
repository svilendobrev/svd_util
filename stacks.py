#sdobrev 2007
# -*- coding: cp1251 -*-
'stack with automatic (ref-counted) cleanup/pop'

class _StackBase( object):
    # Traceback (most recent call last):
    #   ......
    #   File "model\base.pyo", line 46, in <module>
    #   File "engine\timed\setup.pyo", line 7, in <module>
    #   File "util\stacks.pyo", line 82, in <module>
    #   File "util\stacks.pyo", line 83, in Stack
    # TypeError: cannot concatenate 'str' and 'NoneType' objects
    #
    # ne bachka ako nqma __doc__ kato se naprawi EXE !!!

    __doc__ = '''\
стек с автоматичен забърсвач - добавящите методи
връщат обект-забърсвач, който при изчезването си маха последното ниво.
Пример:
$ stack with automatic cleaner - the adding-methods
return object-cleaner, which when destroyed restores the stack/ pops the last level.
Example:
    timestack = Stack( 'time', type=mytype)
    def func1( t):
        c = timestack( mytype( t))
        current = timestack.last()
        print current       #t2
    def func2( t1,t2):
        c = timestack( mytype( t1))
        current = timestack.last()
        print current   #t1
        func1( t2)
        print current   #t1

   stack.last() в/у празен стек вдига IndexError
   stack.last() over empty stack raises IndexError

   ВНИМАНИЕ!:
   $WARNING:
    stack = Stack(...)
    a = stack.push( xx)
    b = stack.push( yy)
   работи както се очаква (последно е yy), докато
   $works as expected (last is yy), while
    d = stack.push( xx)
    d = stack.push( yy)     #същото d!
   няма да направи каквото се очаква - остава xx !!
   $ would not do the expected - xx stays.
''' #XXX

    __slots__ = ('type', 'name')
    def __init__( me, name, type =None):
        me.type = type          #for isinstance
        me.name = name          #only for print

    def push( me, c):
        type = me.type
        if type: assert isinstance( c, type)
        me._stack().append( c)
        return me._StackPtrKeeper( me)
    __call__ = push

    def new( me, *args, **kargs):
        return me.push( me.type( *args, **kargs) )

    def _pop( me): return me._stack().pop()
    def last( me): return me._stack()[-1]
    get=last

    def __str__( me):
        name = me.name
        type = me.type
        stack = me._stack()
        return me.__class__.__name__ + '( %(name)s, type=%(type)s, %(stack)s )' % locals()

    class _StackPtrKeeper( object):
        __slots__ = ( 'stack',)
        def __init__( me, stack): me.stack = stack
        def push( me, *a,**k): return me.stack.push( *a,**k)
        def new(  me, *a,**k): return me.stack.new( *a,**k)
        def last( me): return me.stack.last()
        get = last
        def __str__( me):
            return me.__class__.__name__ + '/' +str( me.stack)
        def restore( me):
            if me.stack: me.stack._pop()
            me.stack = None
        __del__ = restore

###############

class Stack( _StackBase):
    __doc__ = 'plain/обикновен ' + _StackBase.__doc__
    __slots__ = ( '__stack', )
    def __init__( me, *a,**k):
        me.__stack = []
        _StackBase.__init__( me, *a,**k)
    def _stack( me): return me.__stack

import threading

class StackPerThread( _StackBase):
    __doc__ = 'thread-uniq/уникален за нишката ' + _StackBase.__doc__
    __slots__ = ('_stack',)
    _thread_default = threading.local()
    def __init__( me, name, *a,**k):
        _thread_default = me._thread_default
        setattr( _thread_default, name, [])
        me._stack = lambda : getattr( _thread_default, name)
        _StackBase.__init__( me, name, *a,**k)

if __name__ == '__main__':

    mytype = int
    timestack = Stack( 'time', type=mytype)

    def f5():
        tx = timestack.last()
        t5 = tx+14
        c5 = timestack( mytype( t5))
        assert timestack.last() == t5
        c5.restore()
        assert timestack.last() == tx


    def f1( t1,t2):
        c1 = timestack( mytype(t1))
        assert c1.last() == t1
        assert timestack.last() == t1

        c2 = timestack.new( t2)
        assert c1.last() == t2
        assert c2.last() == t2
        assert timestack.last() == t2
        print timestack
        del c2

        assert timestack.last() == t1
        f5()
        assert timestack.last() == t1

    f1( 1,7)
    try:
        timestack.last()
    except IndexError: pass
    else: print 'timestack not empty:', timestack

    try:
        timestack.push( 'boza')
    except AssertionError: pass
    else: print 'typed timestack accepting any type:', timestack

    print timestack.__doc__
# vim:ts=4:sw=4:expandtab
