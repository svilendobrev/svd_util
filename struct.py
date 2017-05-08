#sdobrev 2003-8
'structure as dict as structure, attr-to-item, set-keyword-attrs with allowed/mandatory-validation'

#XXX py3.2 has struct.py in stdlib

class Struct( object):
    'takes any kwargs and turns them into attrs'
    __slots__ = [ '__dict__' ]
    def __init__( me, *a,**k ):
        me.__dict__.update( *a,**k)
    _delimiter_ = '\n'
    def __str__( me, **kargs):      #str( me.__dict__)
        return me._delimiter_.join( [ me.__class__.__name__+'('] +
                          [ '  %s=%s' % kv for kv in me.__dict__.iteritems() ] +
                          [ ')' ] )
    def __eq__( me, other):
        return me.__class__ is other.__class__ and me.__dict__ == other.__dict__
    def __ne__( me, other):
        return not (me==other)
    def clone( me):
        return Struct( me.__dict__)

class Struct_nicestr( Struct):
    __slots__ = ()
    def __str__( me, **kargs):
        from str import make_str
        return make_str( me, me.__dict__, **kargs)

Struct.nicestr = Struct_nicestr

class Struct_debug( Struct):
    __slots__ = ()
    def __setattr__( me, name, value):
        print( '%s=%r' % (name,value))
        Struct.__setattr__( me, name, value)

#######

class DictAttr( dict):
    'getitem == getattr ; like Struct'
    def __init__( me, *a, **k):
        dict.__init__( me, *a, **k)
        me.__dict__ = me
dictAttr = DictAttr

_None = object()  #anything uniq

class attr2item( object):
    'convert getattr/setattr to getitem/setitem'
    __slots__ = [ '_r_', '_default_' ]
    def __init__( me, r =None, default =_None):
        if r is None: r = {}
        me._r_ = r
        me._default_ = default
    def __getattr__( me, k):
        v = getattr( me._r_, k, _None)
        if v is not _None: return v
        #if k in me.__slots__: return me.__getattribute__( k)
        if k in me._r_: return me._r_[k]
        if me._default_ is not _None: return me._default_
        raise AttributeError( k)
        #try: return me._r_[k]
        #except KeyError: raise AttributeError( k)
    def __setattr__( me, k,v):
        if k in me.__slots__: return object.__setattr__( me, k, v)
        return me._r_.__setitem__( k,v)

    def __getitem__( me, k): return me._r_[k]
    def __setitem__( me, k, v): return me._r_.__setitem__( k,v)
    def __delitem__( me, k): return me._r_.__delitem__( k)
##########

class ExtraAttribute(   AttributeError): pass
class MissingAttribute( AttributeError): pass

def set_as_attributes( me, _order =None, _ignore =(),
            _raise_extras  =ExtraAttribute,
            _raise_missing =MissingAttribute,
            _check_missing_by_getattr =False,
            _flat_name ='_order_flat',
            setattr =setattr,
            **kargs):
    """assign ALL keyword args into instance attributes.
        if _order supplied or me has nonempty ._order_flat, follows it.
        if attr in _ignore, is silently ignored
        if _raise_missing / _raise_extras is not set, silently ignores it
        can raise ExtraAttribute, MissingAttribute,
        and ValueError, TypeError etc depending on instance base definition.
    """
    extra = kargs.copy()
    for a in _ignore:
        extra.pop( a, None)

    if _order is None:
        _order = _flat_name and getattr( me, _flat_name, None )
        _order = _order or kargs.iterkeys()

    for a in _order:
        if a in _ignore: continue

        try: v = kargs[ a]
        except KeyError:
            if not _raise_missing: continue
            if _check_missing_by_getattr:
                try: getattr( me, a)
                except AttributeError as e: pass
                else: continue
            raise _raise_missing( a)

        try: setattr( me, a, v)
        except AttributeError as e:
            if _raise_extras:
                import sys
                raise _raise_extras( e.args, sys.exc_info()[2])
        del extra[ a]

    if extra and _raise_extras:
        raise _raise_extras( extra.keys())

# vim:ts=4:sw=4:expandtab
