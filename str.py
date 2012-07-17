#sdobrev 2003-8
'hierarchical str()/print; notSetYet singleton'

#######

class NotSetYet( object):
    def __str__(me): return '<not-set-yet>'
    __repr__ = __str__
    def __new__( klas):     #singleton PLEASE - needs pickle.protocol >=2
        try:
            return notSetYet
        except NameError,e :
            return object.__new__( klas)
#    def __getnewargs__( me): return (True,) #something non empty to distinguish pickling
notSetYet = NotSetYet()

def test_NotSetYet():
    i = NotSetYet()
    assert i is notSetYet
    import pickle
    p = pickle.dumps( i, pickle.HIGHEST_PROTOCOL)
    print repr(p)
    z = pickle.loads(p)
    assert type(z) is type(a)
    assert z is i, ( z,i, id(z), id(i) )

from attr import get_attrib

_level = 0
_stack = []
_make_str_delimiter = '\n'
_make_str_tab = 4*' '
def make_str( me, order, name_name ='name',
                kv_format  ='%s = %r',
                attr_filter =lambda a: a.startswith('__') and a.endswith('__'),
                notSetYet =notSetYet,
                **kargs #getattr =getattr,
    ):
    """ Warning: this may recurse forever if a property calls here,
        AND is listed in the order...
    """
    delimiter = kargs.pop( 'delimiter', _make_str_delimiter)
    tab       = kargs.pop( 'tab', _make_str_tab)
    global _level, _stack
    #print id(me), type(me), _stack
    #if id(me) in _stack: print '*'
    a = ''
    klas_name = me.__class__.__name__
    name = name_name and getattr( me, name_name, None)
    if name and name != klas_name:
        a = name + ': '
    a += klas_name + '('
    if id(me) in _stack:
        return a+'*)'   #round-cycle
    _stack.append( id(me))
    _level+=1
    try:
        r = (delimiter + tab * _level).join( [a]+
                [ kv_format % (k, get_attrib( me, k, notSetYet, **kargs ))
                    for k in order if not attr_filter( k)
                ] )
    finally:
        _level-=1
    r+= delimiter + tab * _level + ')'
    _stack.pop()
    return r

####################

_delimiter = ', '
def str_args_kargs( *args,**kargs):
    delimiter = kargs.pop( '_delimiter', _delimiter)
    repr   = kargs.pop( '_repr', str)
    filter = kargs.pop( '_filter', lambda *a: True)

    return delimiter.join(
        [ repr(a) for a in args ]
        + [ '%s=%s' % (k,repr(v)) for k,v in kargs.iteritems() if filter( k,v) ])

####### debug/log

class printdbg:
    debug =''
    @classmethod
    def callfunc( klas, func, *args,**kargs):
        if 'call' in klas.debug:
            print func, '(\n ', args, '\n  '+ '\n  '.join( '%s=%s' % kv for kv in kargs.iteritems()), '\n)'
        return func( *args, **kargs)

# vim:ts=4:sw=4:expandtab
