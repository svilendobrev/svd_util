# sdobrev 2011
# -*- coding: utf-8 -*-
'dictionaries - attr, key-translating lowercase, map; dictOrder_fromstr'
#all are named dict*

class DictAttr( dict):
    '''attr-access == item-access ; i.e. self.a is self['a']
    >>> d = dictAttr( a=1, b=2)
    >>> d
    {'a': 1, 'b': 2}
    >>> d.a , d['b']
    (1, 2)
    >>> d.c = 3
    >>> d['c']
    3
    '''
    def __init__( me, *a, **k):
        super().__init__( *a, **k)
        me.__dict__ = me

dictAttr = DictAttr

class dict_remover:
    'mixin to a dict-like'
    def remove( me, keys):
        for k in keys: me.pop( k,None)
        return me
    discard = subtract = remove
    def intersect( me, keys):
        return me.remove( set(me)-set(keys))
    only = keep = intersect


#XXX all these are non-associative, i.e. f(a,b) != f(b,a)
def remove( d, keys):
    'overwrite'
    for k in keys: d.pop(k,None)
    return d
discard = remove
def subtract( d, keys):
    'new copy'
    return remove( d.copy(), keys)
    return d.__class__( (k,v) for k,v in d.items() if k not in keys)

def intersection( d, keys):
    'new copy'
    return d.__class__( (k,d[k]) for k in keys if k in d)
def intersect_update( d, keys):
    'overwrite'
    return remove( d, set(d)-set(keys))


def make_dict_lower( base):
    class dict_lower( base):
        'lowercase-keys =~= ignorecase'
        def get( me,k,*default):    return base.get( me, k and k.lower(), *default)
        def pop( me,k,*default):    return base.pop( me, k and k.lower(), *default)
        def __getitem__( me,k):     return base.__getitem__( me, k and k.lower())
        def __contains__( me,k):    return base.__contains__( me, k and k.lower())
        def __setitem__( me,k,v):   return base.__setitem__( me, k and k.lower(), v)
        def __delitem__( me,k):     return base.__delitem__( me, k and k.lower())
        def setdefault( me,k,v):    return base.setdefault( me, k and k.lower(), v)
        def update( me, *args, **kargs):
            seti = me.__setitem__
            if args:
                arg = args[0]
                if isinstance( arg, dict): arg = arg.items()
                for k,v in arg: seti( k,v)    # retain order
            for k,v in kargs.items():
                seti( k,v)      # retain order
        #also fromkeys setdefault copy
    dict_lower.__name__ = base.__name__ + '_lower'
    return dict_lower

dict_lower = make_dict_lower( dict)

import sys  # from .py3
v3 = sys.version_info[0]>=3
if v3: dictOrder = dict
else:
    try:
        from collections import OrderedDict as dictOrder
    except ImportError:
        from dictOrder import dictOrder

def fix_pprint_dict( mydict):
    import pprint
    pprint.PrettyPrinter._dispatch[ mydict.__repr__] = pprint.PrettyPrinter._dispatch[ dict.__repr__]
    #now if len(repr)<width...
    pprint._safe_repr0 = pprint._safe_repr
    pprint._safe_repr = lambda o, *a,**ka: pprint._safe_repr0( (dict(o) if isinstance(o, mydict) else o), *a,**ka)

def fix_pprint_dictOrder(): fix_pprint_dict( dictOrder)

#dict_lower_ordered = make_dict_lower( dictOrder)

############## like DictAttr
class DictAttr_lower( dict_lower):
    'getitem == getattr; ignorecase'
    def __init__( me, *a, **k):
        dict_lower.__init__( me, *a, **k)
        me.__dict__ = me
dictAttr_lower = DictAttr_lower
class DictAttr_lower( dict_lower):
    'getitem == getattr; ignorecase'
    def __init__( me, *a, **k):
        dict_lower.__init__( me, *a, **k)
        me.__dict__ = me
dictAttr_lower = DictAttr_lower

#############

def make_dict_trans( base =dict):
    class dictTrans( base ):
        _stojnost = getattr( base, '_stojnost', '')
        _bez_prevod = set( getattr( base, '_bez_prevod', ()))
        _bez_prevod.update( '_prevodach __dict__'.split() )
        _prevodach = None
        _stojnost = ''
        def __init__( az, *a, **kv):
            super().__init__( *a) # без превод!!
            az._prevodach = kv.pop( '_prevodach')
            az.update_pre( **kv)
        def get( az, k, *defa):
            return super().get( az._prevod( k), *defa )
        def _ima_prevod( az, k):
            return (az._prevodach is not None
                and k not in az._bez_prevod
                and k in az._prevodach)
        def _prevod( az, k, prazno= False):
            return k if not az._ima_prevod( k) else az._prevodach[k]
        def update_pre( az, **kv):
            return az.update( (az._prevod( k),v) for k,v in kv.items() )
        def __getitem__( az, k, *defa):
            assert k not in az._bez_prevod, k
            if not az._ima_prevod( k):
                return super().__getitem__( k)
            r = az.get( az._prevodach[k], *defa )
            if r is None: r = az._stojnost
            return r
        def pop( az, k, deflt =None):
            return super().pop( az._prevod( k), deflt)
        __delitem__ = pop
        def __setitem__( az, k, v):
            assert k not in az._bez_prevod, k
            return super().__setitem__( az._prevod( k ), v)
        def __contains__( az, k):
            return super().__contains__( az._prevod( k))

    dictTrans.__name__ = base.__name__ + '_trans'
    return dictTrans

def make_dict_attr( base =dict):
    class dictAttr( base):
        #_stojnost = getattr( base, '_stojnost', '')
        _bez_prevod = getattr( base, '_bez_prevod', ())
        def __getattr__( az, k):
            try: return az[ k]
            except KeyError: raise AttributeError( k)
            #r = az.get( k, *defa )
            #if r is None: r = az._stojnost
            #return r
        def __delattr__( az, k):
            try: del az[ k]
            except KeyError: raise AttributeError( k)
        def __setattr__( az, k, v):
            if k in az._bez_prevod: return object.__setattr__( az, k, v)
            az[ k ] = v

    dictAttr.__name__ = base.__name__ + '_attr'
    return dictAttr

#########
def dict_fromstr( txt, dict =dict, ignore_comments =True):
    '''format:
        key1 = value 1
        key2 = value 2
    '''
    return dict(
        (a.strip() for a in kv.split('=',1))
        for kv in txt.strip().split('\n')
        if kv.strip() and (not ignore_comments or not kv.strip().startswith('#'))
        )
def dictOrder_fromstr( txt, dict =dictOrder, **ka):
    return dict_fromstr( txt, dict=dict, **ka)

#########
def dict_without( d, *popthese):
    return subtract( d, popthese)
dict_pop = dict_without
#def dict_with( d, **kargs): return dict( d, **kargs)
dict_add = dict_with = dict


if __name__ == '__main__':

    def t0():
        e= DictAttr( a=2)
        assert ( e['a'] == 2 ),e
        assert ( e.a == 2 ) ,e
        assert len(e) == 1  ,e
        e.c=4
        assert ( 'c' in e)  ,e
        assert ( 'd' not in e),e
        assert len(e) == 2  ,e
        assert ( e.c == 4 ) ,e
        assert ( e['c'] == 4 ),e
        e['c']
        print( e)
        #e['d']

        e['c']=3
        assert ( 'c' in e)  ,e
        assert ( e.c == 3 ) ,e
        print( e)

        #e.update_pre( c=3)
        #print(object.__repr__( e))
        #print(object.__repr__( e.__dict__))
        #print(e.c)
        #print(e['c'])
        #print(e['b'])
        #e.b

    t0()
    ######

    def tDictAttrTrans( e):
        assert e['a']==2,e
        assert e.a==2   ,e
        assert 'a' in e ,e
        assert 'aa' not in e ,e
        assert not hasattr( e, 'aaa') ,e
        e.c=4
        assert e['c']==4,e
        assert e.d==4   ,e
        assert e.c==4   ,e
        assert e['d']==4,e
        assert 'd' in e ,e
        assert 'c' in e ,e
        e['c']=3
        assert e.c==3   ,e
        assert e.d==3   ,e
        assert e['c']==3,e
        assert e['d']==3,e
        e.d=5
        assert e.c==5   ,e
        assert e.d==5   ,e
        assert e['c']==5,e
        assert e['d']==5,e

    DictAttrTrans = make_dict_attr( make_dict_trans() )
    e= DictAttrTrans( a=2, _prevodach= dict( c='d') )
    tDictAttrTrans( e)

    DictAttrTrans1 = make_dict_trans(  make_dict_attr() )
    e= DictAttrTrans1( a=2, _prevodach= dict( c='d') )
    tDictAttrTrans( e)

    if 0: #cyk
        DictAttrTrans2 = make_dict_trans( DictAttr)
        e= DictAttrTrans2( a=2, _prevodach= dict( c='d') )
        tDictAttrTrans( e)

    #########

    txt = '''
        a = 4

        b = 5
        #c =6 7
        '''
    d = dictOrder_fromstr( txt, dict= dictOrder)
    assert d == dictOrder( [['a','4'], ['b','5']] ), d
    d = dictOrder_fromstr( txt, dict= dictOrder, ignore_comments =False)
    assert d == dictOrder( [['a','4'], ['b','5'], ['#c','6 7']] ), d

    dab = dict( a=1, b=2)
    dac = dict( a=3, c=2)

    assert subtract( dab, dac) == dict( b=2)
    assert remove( dab.copy(), dac) == dict( b=2)

    assert intersection( dab, dac) == dict( a=1)
    assert intersection( dac, dab) == dict( a=3)
    assert intersect_update( dab, dac) == dict( a=1)

# vim:ts=4:sw=4:expandtab
