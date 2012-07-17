#!/usr/bin/env python
# sdobrev 2012
'generate a (wiki) page from first __doc__ lines of input python yfiles (e.g. for github)'

import optz,sys
optz.text( 'pfx',       help= 'base prefix for all links',)
optz.bool( 'link',      help= 'show as [[name|link]]' )
optz.text( 'unprefix',  help= 'strip this prefix from input file names' )

optz,args = optz.get()
quotes = '"\''
items = {}
for f in args:
    opened = False
    for a in open(f):
        a = a.strip()
        if not a or a[0]=='#': continue
        if a[0] in quotes or opened:
            a = a.strip( quotes)
            if not a:
                opened = True
                continue

            items[f] = a
            break
    else:
        print >>sys.stderr, '? no description:', f

#print '\n'.join( k+': '+v for k,v in sorted( items.items()))
for k,v in sorted( items.items()):
    if optz.unprefix:
        if k.startswith( optz.unprefix): k = k[ len(optz.unprefix):].lstrip('/')
    link = optz.pfx+k
    if optz.link: link = '[['+k+'|'+link+']]'
    print '*', link, ':', v

# vim:ts=4:sw=4:expandtab
