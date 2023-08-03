#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# sdobrev 2004-8
from __future__ import unicode_literals

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
            #print( 33, c, m)
            if m is None and l>1: continue
            x= x[l:]
            r+= m or c
            break
    return r

def dec(x): return x and x.decode( 'cp1251')
#def low2up( k): return ''.join( chr(ord(kk)-32) for kk in k)
def capital(v): return v and v[0].upper()+v[1:]

def make( cyr =(), lat =(), cyr2lat ={}, lat2cyr ={} ):
    if 0 :#not _v3:
        cyr = dec( cyr)
        lat = dec( lat)
        cyr2lat = dict( (dec(k), dec(v)) for k,v in cyr2lat.items())

    c2l = dict( (k, v.split('|')[0]) for k,v in cyr2lat.items())
    l2c = dict( (vv,k)
                for k,v in cyr2lat.items()
                for vv in v.split('|')
                if vv
                )
    c2l.update( [(capital(k), capital(v)) for k,v in c2l.items()])
    l2c.update( [(capital(k), capital(v)) for k,v in l2c.items()])
    l2c.update( lat2cyr)
    l2c.update( [(capital(k), capital(v)) for k,v in lat2cyr.items()])

    cl = dict( zip( cyr,lat ) )
    cl.update( (capital(k), capital(v)) for k,v in zip( cyr,lat ) )

    c2l.update( cl )
    l2c.update( (v,k) for k,v in cl.items() if v )  #override
    return c2l,l2c


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
        #'ьо': 'io|yo',
        'ьо': 'yo',
        #'ай': 'ay',
        #'ей': 'ey',
        #'ой': 'oy',
        #'ий': 'iy',
        #'уй': 'uy',
        'ѝ': 'i',
        'ь': '',
        'ъ': 'y',
        'ю': 'yu|ju',
        'я': 'ya|ja|q',
        'ая': 'aia',
        'ия': 'iia',
        'eя': 'eia',
        'oя': 'oia',
        'уя': 'uia',
        'э': 'ye',
        'ы': 'yi',
        'в': 'w',
        },
        lat2cyr = {
        'x': 'кс',
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

class digito_fonetic( transliterator):
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
    nm = sys.argv[0]
    l2c = 'lat2cyr' in nm
    import optparse
    oparser = optparse.OptionParser()
    def optany( name, *short, **k):
        return oparser.add_option( dest=name, *(list(short)+['--'+name.replace('_','-')] ), **k)
    def optbool( name, *short, **k):
        return optany( name, action='store_true', *short, **k)

    optbool( 'cyr2lat', )
    optbool( 'c2l', )
    optbool( 'lat2cyr', )
    optbool( 'l2c', )
    optbool( 'utf', )
    optbool( 'iutf', )
    optbool( 'outf', )
    optbool( 'o1251', )
    optbool( 'cp1251', )
    optbool( 'org', )
    optbool( 'rename',      help='преименува файлове, запазва .ext')
    optbool( 'symrename',   help='преименува само символични връзки - къде сочат, целите')
    optbool( 'extrename',   help='превежда и .ext -> .еьт')
    tmap = dict( (c.__name__, c) for c in transliterator.__subclasses__() )
    optany( 'map', type= 'choice', choices= sorted( tmap), default= zvuchene.__name__,
                help='преводач: [%default] ; едно от: '+' '.join(sorted(tmap)))

    opts,args = oparser.parse_args()
    if opts.cyr2lat or opts.c2l: l2c=0
    if opts.lat2cyr or opts.l2c: l2c=1
    utf = opts.utf and not _v3
    iutf = opts.iutf and not _v3 or utf
    outf = opts.outf and not _v3 or utf
    o1251= (opts.cp1251 or opts.o1251) and not _v3
    org = opts.org
    rename = opts.rename
    renext = opts.extrename
    map = tmap[ opts.map ]

    import os
    convert = getattr( map, l2c and 'lat2cyr' or 'cyr2lat' )

    for l in (args if rename else sys.stdin):
        try:
            l = l.rstrip()
            ext=''
            if rename:
                l = l.rstrip('/')
                if opts.symrename:
                    if not os.path.islink( l):
                        print( '!ignore non-symlink', l)
                        continue
                    lorg = l
                    #path,lorg = os.path.split( l)
                    l = os.readlink( l)
                else:
                    path,l = os.path.split( l)
                if not renext: l,ext = os.path.splitext( l )
            else: path = None
            if iutf: l = l.decode('utf8')
            r = convert(l)
            if outf: r = r.encode('utf8')
            elif o1251: r = r.encode('cp1251')
            if not rename or l!=r:
                if org: sys.stdout.write( l +' = ')
                sys.stdout.write( r+'\n')
            if rename and l!=r:
              if opts.symrename:
                os.remove( lorg)
                os.symlink( r+ext, lorg)
              else:
                l = os.path.join( path,l)+ext
                r = os.path.join( path,r)+ext
                try:
                    os.rename( l, r)
                except:
                    print( '?', l, '-->', r)
                    raise
        except:
            print( '????????', l.encode( 'utf8', errors='backslashreplace'))
            raise

# vim:ts=4:sw=4:expandtab
