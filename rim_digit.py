#!/usr/bin/env python
# -*- coding: utf-8 -*-
'rome digits to numeric'

from __future__ import print_function, unicode_literals

re_nomer = '(\d+|[ivxIVX]+)'

rim = dict( I=1, II=2, III=3, IV=4, V=5, VI=6, VII=7, VIII=8, IX=9, X=10)
rim.update( [('X'+k,10+v) for k,v in rim.items() ])

I= '\u0406' # u'І'ne-lat ne-cyr
X= '\u0425' # u'Х'cyr
def rim2fix( nomer, doX =True):
    r = nomer.replace( I,'I')
    if doX: r = r.replace( X,'X')
    return r
#).replace( '\u2013','-'     #-

def rim2int( nomer, *default):
    return rim.get( nomer.upper(), *default)

if __name__ == '__main__':
    import re, sys, os, locale
    def repl( m):
        x = m.group(1)
        f = rim2int(x)
        return f and str( f) or x
    for f in sys.argv[1:]:
        a = f.decode( locale.getpreferredencoding() )
        a = rim2fix(a)
        b = re.sub( re_nomer, repl, a, 1)
        if b != a:
            print( ' ', f)
            print( '>', b)
            os.rename( f,b)

# vim:ts=4:sw=4:expandtab
