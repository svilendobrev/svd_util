#!/usr/bin/env python
#$Id: moddump.py,v 1.2 2007-02-27 23:18:07 sdobrev Exp $
##svilen.dobrev.2k2
import sys
import pprint

def docdump(modname):
    mod = __import__( modname )

    print "module:", modname
    try:
        print modname+".__file__:", mod.__file__
    except AttributeError: print "undefined, probably built-in"

    print "\n-----------", modname+ ".__doc__: -------------"
    print mod.__doc__

    print "\n-----------", modname+ ".__dict__: -------------"
    pprint.pprint( mod.__dict__ )

    print "\n-----------", modname+ ".item's __doc__s: -------------"
    dic = mod.__dict__
    items = dic.keys()
    items.sort()
    for k in items:
        try:
            doc = dic[k].__doc__
            print "-----", k
            print doc
        except AttributeError:
            pass
    print "=================="

sys.path.insert( 0, '.')
print "module-search-path:"
pprint.pprint( sys.path )

try:
    modname = sys.argv[1]
    docdump( modname )
except IndexError:
    print "use:", sys.argv[0], "module_name"

# vim:ts=4:sw=4:expandtab
