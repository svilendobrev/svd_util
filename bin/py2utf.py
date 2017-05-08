#!/usr/bin/env python
# -*- coding: utf-8 -*-
#sdobrev 2012

'''
autoconvert (source-files) from cp1251 to utf AND fix the "coding" line

преобразува (файлове) от 1251 в УТФ и оправя реда за "coding"
'''
try:
    from svd_util import eutf, optz
except:
    import os.path, sys
    p = os.path.realpath( __file__).split('/')
    sys.path.insert( 0, '/'.join( p[:-2]) )
    import eutf,optz #hope it lives in ..

import os, sys, re

optz.bool( 'keeputf',   help= 'keep "coding utf" line even if file is ascii')
optz.bool( 'forceutf',  help= 'add  "coding utf" line even if file is ascii')
optz.bool( 'dirsymlink',    help= 'walk symlink dirs')
optz.bool( 'symlink',       help= 'walk symlink files')
optz.bool( 'doit',      help= 'do overwrite')

optz,args = optz.get()

re_c = re.compile( '^#.*?coding\s*[=:]\s*([-\w.]+)')
u8 = 'utf-8'

def walker( a):
    if not os.path.isdir( a):
        yield '', a
    else:
        for path, dirs, files in os.walk( a, followlinks= optz.dirsymlink):
            for f in files:
                fp = os.path.join( path, f)
                yield path, f

if __name__ == '__main__':
    for a in args:
        for path, f in walker( a):
            if not f.endswith( '.py'): continue
            fp = os.path.join( path, f)
            if not optz.symlink and os.path.islink( fp): continue
            #f,enc = open_detect( fp).read()
            data = open( fp).read()
            ascii = False
            utfs = ['utf-8', 'utf8']
            try:
                r = data.decode( 'ascii')
                enc = None
            except:
                try:
                    r = data.decode( u8)
                    enc = u8
                except:
                    r = data.decode( 'cp1251')
                    enc = 'cp1251'

            lines = r.split('\n')
            rs = []
            found = 0
            encline = enc and '# -*- coding: '+u8+' -*-' or ''
            N=2
            hdr = lines[:N]
            encs = hdr[:]       #copy
            found = None
            for i,a in enumerate( hdr):
                m = re_c.search( a)
                if not m: continue
                if found:   #repeated?
                    encs[i] = ''
                    continue
                menc = m.group(1).lower()
                found = menc
                if menc in utfs:
                    if enc or optz.keeputf:
                        continue #is what will become or ascii as utf
                encs[i] = encline
            #print '    ', fp, found, encs

            if not found:
                #not found
                if not enc and not optz.forceutf:
                    continue    #nothing to do - dont touch
                l0busy = hdr[0].startswith('#')
                encs.insert( int(l0busy), encline)

            r = '\n'.join( encs + lines[N:] ).encode( u8)
            if r == data:
                continue    #nothing to do - dont touch
            print(fp, 'is:', enc, 'found:', found, encs==hdr and 'hdrsame' or 'hdrdiff', 'new:', encs)
            if optz.doit:
                with open( fp, 'w') as o:
                    o.write( r)

# vim:ts=4:sw=4:expandtab
