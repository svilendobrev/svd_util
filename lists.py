
def appendif( lst, *oo):
    for o in (oo or ()):
        if o not in lst: lst.append( o)
    return lst

def extendif( lst, oo): return appendif( lst, *(oo or ()))

import collections
def setorder( *a):
    r = []
    if len(a)==1 and isinstance( a[0], collections.Iterable): #(list,tuple,dict)):
        a = a[0]
    return extendif( r, a )
listif = setorder

# vim:ts=4:sw=4:expandtab
