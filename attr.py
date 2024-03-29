#s.dobrev 2k4-6

'''
additional python-reflection tools:
- multilevel getattr, setattr, import, getitemer
- local vs see-through-hierarchy getattr
- fail-proof issubclass()
- subclasses extractor
- func_attrs decorator
'''
#from py3 import basestring
import sys
if sys.version_info[0]>=3: basestring = str

def set_attrib( self, name, value, getattr =getattr, setattr=setattr):
    'setattr over hierachical name'
    if isinstance( name, basestring):
        name = name.split('.')
    name1 = name[-1]
    if len(name)>1:
        for a in name[:-1]:
            self = getattr( self, a)
    setattr( self, name1, value )

def get_attrib( self, name, *default_value, **kargs):
    'getattr over hierachical name'
    if isinstance( name, basestring):
        name = name.split('.')
    _getattr = kargs.get( 'getattr', getattr)
    _Error = kargs.get( 'error', AttributeError)
    for a in name:
        try:
            self = _getattr( self, a)
        except _Error:
            if not default_value: raise
            return default_value[0]
    return self
    #if name.find('.')>0: return eval( 'self.'+name )
    #return getattr( self, name)


def get_item( d, name, *default_value, **kargs):
    'get_attrib but for dict/indexable - full'
    #from operator import getitem
    def _getter( d,k):
        if not hasattr( d, '__getitem__'): raise KeyError
        return d[k]
    kargs.setdefault( 'getattr', _getter) #lambda d,k: d[k] )
    kargs.setdefault( 'error', KeyError)
    return get_attrib( d, name, *default_value, **kargs)

def get_item_( d, kmulti):
    'get_attrib but for dict/indexable - quick'
    for a in kmulti.split('.'): d = d[a]
    return d


class get_itemer:
    '''dict simulator for hierarchical names/lookups:
       use: "%(a.b.c.d)s %(e)s" % get_itemer( locals() ) '''
    def __init__( me, d): me.d = d
    def __getitem__( me, k):
        names = k.split('.', 1)
        r = me.d[ names[0] ]
        if len(names)>1:
            r = get_attrib( r, names[1] )
        return r


#######
# getattr(klas) looks up bases! hence use __dict__.get

def getattr_local_instance_only( me, name, *default_value):
    'lookup attr in instance, and not in class/bases'
    try:
        return me.__dict__[ name]
    except KeyError:
        if not default_value: raise AttributeError( name)
        return default_value[0]

def getattr_local_class_only( me, name, *default_value):
    'lookup attr in leaf class, and not in instance nor in bases'
    try:
        return me.__class__.__dict__[ name]
    except KeyError:
        if not default_value: raise AttributeError( name)
        return default_value[0]

def getattr_local_instance_or_class( me, name, *default_value):
    'lookup attr in instance or leaf class, but not in base classes'
    try:
        return me.__dict__[ name]
    except KeyError:
        return getattr_local_class_only( me, name, *default_value)

#'lookup attr in instance, leaf class, or any bases
getattr_global = getattr

def getattr_in( me, local =True, klas =True, *a,**k):
    'lookup attr in all ways'
    if local and klas:
        return getattr_local_instance_or_class( me, *a,**k)
    if local:
        return getattr_local_instance_only( me, *a,**k)
    if klas:
        return getattr_local_class_only( me, *a,**k)
    return getattr_global( me, *a,**k)     #plain getattr with all the lookup

#######

def setattr_kargs( *args, **kargs):
    '''set all kargs key/values as attrs;
    e.g.
    def __init__( me, someflag, **kargs):
        setattr_kargs( me, **kargs)
        if someflag: whatever
    or
    __init__ = setattr_kargs
    or just copy the last line instead of calling this
    '''
    assert len(args)==1
    me = args[0]
    for k,v in kargs.iteritems(): setattr( me, k, v)

#######

def setattr_from_kargs( me, inkargs, **kargs):
    '''from inkargs, pop those in kargs using the values as defaults, and setattr
    e.g.
    def func( me, **kargs):
        setattr_from_kargs( me, kargs, ala=1, bala=2, nica=3)
        super(me).func( **kargs)
    instead of:
    def func( me, ala=1, bala=2, nica=3, **kargs):
        me.ala=ala
        me.bala=bala
        me.nica=nica
        super(me).func( **kargs)
    '''
    for k,v in kargs.iteritems():
        setattr( me, k, inkargs.pop( k, v) )

#######

def setattr_kargs_in_order( me, these_first =(), **kargs):
    for k in these_first:
        if k in kargs:
            #print '>>',k,kargs[k]
            setattr( me, k, kargs.pop( k) )
    setattr_kargs( me, **kargs)

########

def getattr_each_by_inheritance( klas, name,
        without_self =False,
        order_flattened =(),    #__mro__ by default; careful, this should be leaf-to-root
        getattr =getattr,   #=getattr: yields at first visible place (leaf-most)
                            #=getattr_local_instance_only: yields at place of declaration (root-most)
    ):
    '''for rich multiple inheritance, define things locally, then use this to collect them all
       e.g. many have local setup() methods - single setup_all() can call them all without omissions
    '''
    used = set()
    notfound = used
    for k in order_flattened or klas.__mro__:
        k = k or klas   #None means self
        if without_self and k is klas: continue
        f = getattr( klas, name, notfound)
        if f is not notfound and f not in used:
            used.add(f)
            yield f

########

def flatten_vars( klas, ignore_hidden=True):
    res = {}
    for dic in reversed( [ vars(k) for k in klas.mro() ] ):
        res.update( dic)
    if ignore_hidden:
        return dict( (k,v) for k,v in res.iteritems() if not k.startswith('__'))
    return res


# util/base.py
try:
    from types import ClassType
    _classtypes = (type, ClassType)
except:
    _classtypes = (type, )
def isclass( obj):
     return isinstance( obj, _classtypes)
__issubclass = issubclass
def issubclass( obj, klas):
    'fail/fool-proof issubclass() - works with ANY argument'
    return isclass( obj) and __issubclass(obj, klas)


def isiterable( obj, string_is_iterable =False):
    if isinstance( obj, basestring):
        return string_is_iterable
    try:
        iter( obj)
    except TypeError:
        return False
    return True


def iscollection( obj):
    return isinstance( obj, (list, tuple, set))

def subclasses_in( locals, base_klas, module_name =None, exclude =(), include_base =False):
    if isinstance( locals,dict): all = locals.values()
    else: all = locals
    return sorted( #dict( (c.__name__, c) for c in
            set( c
            for c in all
            if ( issubclass( c, base_klas)
             and (not module_name or c.__module__ == module_name)
             and c not in exclude
             and (c is not base_klas or include_base)
            ) )
        , key= lambda c: c.__name__)

def subclasses( klas):
    'ALL subclasses of klas but klas itself ; breadth-first; non-recursive'
    subklasi = []
    klasi = [klas]
    while True:
        x = []
        for k in klasi:
            x += k.__subclasses__()
        if not x: break
        for y in x:
            if y not in subklasi: subklasi.append(y)
        klasi = x
    return subklasi

def all_subclasses_of( klas):
    'ALL subclasses of klas but klas itself ; depth-first ; recursive'
    res = []
    for sub in klas.__subclasses__():
        res.append(sub)
        res += all_subclasses_of(sub)
    return res

class anymethod( object):
    '''wrapper that calls func with/via whatever it is called
        - either klas or instance - unlike classmethod, e.g.
class X:
    @anymethod
    def printer( inst_or_klas, args): print inst_or_klas, args

>>> X.printer( 5)
__main__.X 5
>>>
>>> X().printer( 6)
<__main__.X instance at 0xb74983ac> 6
    '''
    def __init__( me, func): me.func = func
    def __get__( me, obj, klas ):
        if obj is None: obj = klas
        return lambda *a,**ka: me.func( obj, *a,**ka)

def inspect_methods( klas, filter_out =lambda name: name.startswith( '_') ):
    'ret { klas: { name: func }}'
    import inspect
    methods = {}
    for name in dir( klas):
        if filter_out and filter_out( name): continue
        m = getattr( klas, name)
        if not inspect.ismethod( m): continue

        for kl in klas.mro():
            if name in kl.__dict__:
                methods.setdefault( kl, {})[ name] = m
                break
    return methods

def func_attrs( **ka):
    '''@func_attrs( label='hey')
    def ...
    '''
    def deco( f):
        for k,v in ka.items(): setattr( f,k,v)
        return f
    return deco

########
# util/module.py

def import_fullname( name, last_non_modules =0, **kargs):
    'replacement of __import__ returning the leaf module'
    subnames = name.split('.')
    if last_non_modules:
        name = '.'.join( subnames[:-last_non_modules])
    m = __import__( name, **kargs)
    for k in subnames[1:]: m = getattr(m,k)
    return m

def find_valid_fullname_import( paths, last_non_modules =1):
    'search for a valid attribute path, importing them if needed'
    if isinstance( paths, basestring): paths = paths.split()
    for p in paths:
        try:
            return import_fullname( p, last_non_modules=last_non_modules)
        except Exception as e:
#            print e
            pass
    assert 0, 'cant find any of ' + str(paths)

# vim:ts=4:sw=4:expandtab
