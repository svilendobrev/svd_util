#!/usr/bin/env python3
# -*- coding: cp1251 -*-
# sdobrev 2004-8
'cyrillic transcripting to/from latin - e.g. qwerty, SMS, sounds-like, looks-like, etc'

import sys
_v3 = sys.version_info[0]>=3

def direct( map, x): return ''.join( map.get(a,a) for a in x )

def do321( map, x):
    r = ''
    while x:
        for l in 3,2,1:
            c= x[:l]
            m= map.get( c)
            if m is None and l>1: continue
            x= x[l:]
            r+= m or c
    return r

def dec(x): return x and x.decode( 'cp1251')

def make( cyr =(), lat =(), cyr2lat ={} ):
    if not _v3:
        cyr = dec( cyr)
        lat = dec( lat)
        cyr2lat = dict( (dec(k), dec(v)) for k,v in cyr2lat.items())

    c2l = cyr2lat.copy()
    c2l.update( (k.upper(), capital(v)) for k,v in cyr2lat.items())

    l2c = {}
    for k,v in c2l.items():
        if '|' in v:
            vs = v.split('|')
            c2l[k] = vs[0]
            for vv in vs:
                l2c[vv]=k
        elif v:
            l2c[v]=k

    cl = dict( zip( cyr,lat ) )
    cl.update( (k.upper(), capital(v)) for k,v in zip( cyr,lat ) )

    c2l.update( cl )
    l2c.update( (v,k) for k,v in cl.items() if v )  #override
    return c2l,l2c

#def low2up( k): return ''.join( chr(ord(kk)-32) for kk in k)
def capital(v): return v and v[0].upper()+v[1:]

class transliterator:
    @classmethod
    def dump( me):
        print( 'cyr2lat:', ' '.join( k+':'+v for k,v in me.cyr2lat.items() ))
        print( 'lat2cyr:', ' '.join( k+':'+v for k,v in me.lat2cyr.items() ))
    @classmethod
    def cyr2lat( me, x): return do321( me._cyr2lat, x)
    @classmethod
    def lat2cyr( me, x): return do321( me._lat2cyr, x)

class zvuchene( transliterator):
    _cyr2lat,_lat2cyr = make(
        cyr= 'абвгдезийклмнопрстуфхц',
        lat= 'abvgdezijklmnoprstufhc',
        cyr2lat = {
        'ж': 'zh',
        'ч': 'ch',
        'ш': 'sh',
        'щ': 'sht',
        'ьо': 'io|yo',
        'ь': '',
        'ъ': 'y',
        'ю': 'iu|yu',
        'я': 'ia|ya',
        'э': 'e',
        'ы': 'i',
        'в': 'w',
        })

class special2plain( transliterator):
    #py3: u0085 isspace() but not in string.whitespace?
    _lat2cyrz = dec( b'''\
\x82    ,
\x84    "
\x85    ...
\x8b    <
\x91    '
\x92    '
\x93    "
\x94    "
\x95    *
\x96    -
\x97    -
\x99    (tm)
\x9b    >
\xab    <<
\xbb    >>
\xa9    (c)
\xa6    |
\xb1    +/-
\xb9    No.
\xb2    I
\xb3    i
\xbc    j
\xa3    J
\xbd    S
\xbe    s
''')
    _lat2cyr = dict( ab.split() for ab in _lat2cyrz.strip().split( '\n') )
    _cyr2lat = dict( (v,k) for k,v in _lat2cyr.items())
    more = b'''
\xb0    degree
\xb5    micro
\xa7    paragraph
\xb6    pi
'''


class zvuchene_qw( transliterator):
    _cyr2lat,_lat2cyr = make(
        cyr= 'абвгдезиклмнопрстуфхц',
        lat= 'abwgdeziklmnoprstufhc',
        cyr2lat = {
        'й': 'i',
        'ж': 'j',
        'ч': 'ch',
        'ш': 'sh',
        'щ': 'sht',
        'ьо': 'jo',
        'ь': '',
        'ъ': 'y',
        'ю': 'iu|ju',
        'я': 'iu|ju',
        'э': 'e',
        'ы': 'i',
        'в': 'v',
        })

class qwerty_keyboard( transliterator):    #fonetic
    _cyr2lat,_lat2cyr = make(
        cyr= 'абвгдежзийклмнопрстуфхц',
        lat= 'abwgdevzijklmnoprstufhc',
        cyr2lat = {
        'ч': '`',
        'ш': '[',
        'щ': ']',
        'ь': '',
        'ъ': 'y',
        'ю': '\\\\',
        'я': 'q',
        'э': '@',
        'ы': '^',
        })

class qwerty_keyboard_yu( transliterator):   #fonetic
    _cyr2lat,_lat2cyr = make(
        cyr= 'абвгдежзиклмнопрстуфхц',
        lat= 'abvgde`ziklmnoprstufhc',
        cyr2lat = {
        #'й':'j',
        '-': 'j',
        'ч': '~',
        'ш': '{',
        'щ': '}',
        'ь': '',
        'ъ': 'y',
        'ю': '\\\\',
        'я': 'q',
        'э': '@',
        'ы': '^',
        })

class desi( transliterator):   #digito-fonetic
    _cyr2lat,_lat2cyr = make(
        cyr= 'абвгдежзийклмнопрстуфхц',
        lat= 'abvgdejziiklmnoprstufhc',
        cyr2lat = {
        'ч': '4',
        'ш': '6',
        'щ': '6t',
        'ь': '',
        'ъ': 'y',
        'ю': 'iu',
        'я': 'ia',
        'э': '@',
        'ы': '^',
        })

if __name__ == '__main__':
    import sys
    nm = sys.argv.pop(0)
    l2c = 'lat2cyr' in nm
    def opt(*xx):
        for x in xx:
            try: sys.argv.remove( x ); return True
            except ValueError: continue
        return None
    if opt( '-h', '--help'):
        print( '''\
-c2l -cyr2lat
-l2c -lat2cyr
-iutf
-outf
-org        org = new
-special    special2plain ; else zvuchene
        ''')
        raise SystemExit
    if opt( '--cyr2lat', '--c2l', '-c2l'): l2c = 0
    if opt( '--lat2cyr', '--l2c', '-l2c'): l2c = 1
    utf = opt( '--utf') and not _v3
    iutf = opt( '-iutf', '--iutf') and not _v3 or utf
    outf = opt( '-outf', '--outf') and not _v3 or utf
    o1251= opt( '-1251', '--1251', '--cp1251', '-cp1251') and not _v3
    org = opt( '--org')
    rename = opt( '--rename')

    if opt( '-special'): map = special2plain
    else: map = zvuchene

    convert = getattr( map, l2c and 'lat2cyr' or 'cyr2lat' )

    for l in (sys.argv if rename else sys.stdin):
        l = l.rstrip()
        if iutf: l = l.decode('utf8')
        r = convert(l)
        if outf: r = r.encode('utf8')
        elif o1251: r = r.encode('cp1251')
        if not rename or l!=r:
            if org: sys.stdout.write( l +' = ')
            sys.stdout.write( r+'\n')
        if rename and l!=r:
            import os
            try:
                os.rename( l, r)
            except:
                print( '?', l, '-->', r)
                raise

# vim:ts=4:sw=4:expandtab
