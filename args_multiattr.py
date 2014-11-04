#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

def args_as_multiattr( args, all_attrs, trigger_attr):
    all = []
    errors = []
    d = dict.fromkeys( all_attrs)
    for i in args:
        kv = i.split('=',1)
        if len(kv)!=2:
            errs.append( ('wrong arg', i))
            continue
        k,v = kv
        if k not in d:
            errors.append( ('wrong arg-attr', i, '; use one of', all_attrs))
            continue

        d[k] = v
        if k == trigger_attr:
            if None in d.values():
                errors.append( ('wrong arg-order around', i))
                continue
            all.append( dict(d))

    if all and all[-1] != d:
        errors.append( ('wrong arg-order at end',))
    return all,errors

def help( attrs, trigger_attr ):
    attrs = list( attrs)
    attrs.remove( trigger_attr)
    attrs.append( trigger_attr)
    orred = '=.. or '.join( attrs) + '=..'
    a = 'a'
    b = 'b'
    tr = trigger_attr
    return '''\
one or multiple of: %(orred)s ;
%(trigger_attr)s yields, others attrs apply to all later yields. Example:
%(a)s=X %(b)s=A %(tr)s=1 %(tr)s=2 %(a)s=Y %(tr)s=3 %(b)s=B %(tr)s=4 %(tr)s=5
-> (1,X,A), (2,X,A), (3,Y,A), (4,Y,B), (5,Y,B)
'''.strip() % locals()

if __name__ == '__main__':
    #use as argparse/nargs=* or else
    attrs = 'klas file level'.split()
    trigger_attr = attrs[1]
    print( help( attrs, trigger_attr))

    oks = '''
        klas=k1 level=l1 file=f1 klas=k2 level=l2 file=f2  level=l3 file=f3 file=f4 klas=k5 file=f5
        klas=aa level=L1 file=f1 file=f2 klas=bb file=f3 level=L2 file=f4
    ''',True
    errs = '''
        file=f1 klas=k1 level=l1 file=f2 klas=k2 level=l2
        klas=k1 level=l1 file=f1 file=f2 klas=k2 level=l2
    ''',False

    for tests,ok in [oks, errs]:
        for t in tests.strip().split('\n'):
            print( ok and 'ok:' or 'err:', t.strip())
            n = t.split()
            #print( ' ', n)
            all,errors = args_as_multiattr( n, all_attrs= attrs, trigger_attr= trigger_attr)
            for a in all: print( ' ', a)
            for e in errors: print( '!err:', *e)

# vim:ts=4:sw=4:expandtab
