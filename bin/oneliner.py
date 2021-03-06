#!/usr/bin/env python
# sdobrev 2012
'generate a (wiki) page from first __doc__ line/para of input python files (e.g. for github)'

try:
    from svd_util import optz
except:
    import os.path, sys
    p = os.path.realpath( __file__).split('/')
    sys.path.insert( 0, '/'.join( p[:-2]) )
    import optz #hope it lives in ..

import sys, os
optz.text( 'base',      help= 'base prefix for all links',)
optz.bool( 'wikilink',  help= 'show as [[name|link]]' )
optz.bool( 'mdlink',    help= 'show as [name](link)' )
optz.bool( 'para',      help= 'get whole first paragraph' )
optz.text( 'unprefix',  help= 'strip this prefix from input file names' )

optz,args = optz.get()
quotes = '"\''
items = {}
for f in args:
    opened = False
    for a in open(f):
        a = a.strip()
        if not a:
            if opened: break
            continue
        if not opened:
            if a[0]=='#': continue
            if a[0] in quotes:
                opened = a[0]
                if a[:3].count( opened)==3:
                    opened = a[:3]
                a = a[ len(opened): ]   # a = a.strip( quotes)
                a = a.strip()

                if not a:
                    continue
        if opened:
            if a.endswith( opened):
                a = a[ :-len( opened)]
                opened = False
            items[f] = (items.get( f, '') + ' ' + a ).strip()
            if not opened or not optz.para:
                break
    else:
        print('? no description:', f, file=sys.stderr)

#print '\n'.join( k+': '+v for k,v in sorted( items.items()))
for k,v in sorted( items.items()):
    if optz.unprefix:
        if k.startswith( optz.unprefix): k = k[ len(optz.unprefix):].lstrip('/')
    pp = list( os.path.split( k))
    try:
        pp.remove( '__init__.py')
    except: pass
    else:
        k = os.path.join( *pp)+'/'
    link = optz.base + k
    if optz.wikilink: link = '[['+k+'|'+link+']]'
    elif optz.mdlink: link = '['+k+']('+link+')'
    print('*', link, ':', v)

# vim:ts=4:sw=4:expandtab
