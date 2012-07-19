# sdobrev 2011
'key-translating dictionaries - lowercase, map; dictOrder_fromstr'

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

############## like struct.DictAttr
class DictAttr_lower( dict_lower):
    'getitem == getattr; ignorecase'
    def __init__( me, *a, **k):
        dict_lower.__init__( me, *a, **k)
        me.__dict__ = me

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
        def __delitem__( az, k):
            return az.pop( az._prevod( k), None )
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
        _bez_prevod = getattr( base, '_bez_prevod', '')
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
def dictOrder_fromstr( txt, dictOrder =dict):
    '''format:
        key1 = value 1
        key2 = value 2
    '''
    return dictOrder( #dict
        (
        (a.strip() for a in kv.split('='))
        for kv in txt.strip().split('\n') ))



if __name__ == '__main__':

    from util.struct import DictAttr
    def t0():
        e= DictAttr( a=2)
        e.c=4
        print( 'c' in e)
        print( 'd' in e)
        e['c']
        print( e)
        #e['d']

        e['c']=3
        print( 'c' in e)
        print( e)

        #e.update_pre( c=3)
        #print(object.__repr__( e))
        #print(object.__repr__( e.__dict__))
        print(e.c)
        print(e['c'])
        #print(e['b'])
        #e.b

    #t0()

def tDictAttrTrans( e):
    assert e['a']==2
    assert e.a==2
    assert 'a' in e
    assert 'aa' not in e
    assert not hasattr( e, 'aaa')
    e.c=4
    assert e['c']==4
    assert e.d==4
    assert e.c==4
    assert e['d']==4
    assert 'd' in e
    assert 'c' in e
    e['c']=3
    assert e.c==3
    assert e.d==3
    assert e['c']==3
    assert e['d']==3
    e.d=5
    assert e.c==5
    assert e.d==5
    assert e['c']==5
    assert e['d']==5

    DictAttrTrans = make_dict_attr( make_dict_trans() )
    e= DictAttrTrans( a=2, _prevodach= dict( c='d') )
    tDictAttrTrans( e)

    DictAttrTrans1 = make_dict_trans(  make_dict_attr() )
    e= DictAttrTrans1( a=2, _prevodach= dict( c='d') )
    tDictAttrTrans( e)

    DictAttrTrans2 = make_dict_trans( DictAttr)
    e= DictAttrTrans2( a=2, _prevodach= dict( c='d') )
    tDictAttrTrans( e)

# vim:ts=4:sw=4:expandtab
