#!/usr/bin/env python
##
from __future__ import print_function

def getpaths( data, paths):
    'extract from dict by multiple key-paths: [ [ str|list, str|list, ...] ] '
    r = {}
    for p in paths:
        r.update( getpath( data, p))
    return r

def getpath( data, path):
    'extract from dict by key-path: [ str|list, str|list, ...] ; each level is single key or multiple keys/OR'
    if not path: return data
    r = {}
    i = path[0]
    for e in (i if isinstance( i, (list,tuple)) else [ i ]):
        r[e] = getpath( data.get(e), path[1:] )
    return r


if __name__ == '__main__':
    import sys
    sys.path.pop(0) #XXX HACK avoid cur dir .. because struct.py
    from couchdb import Server
    server = Server( sys.argv[1])
    data = server.stats()
    paths = [
        [ 'couchdb', 'database_writes', 'current' ], #this misses db-create/delete. even with couchdb/open_databases
        [ 'httpd_request_methods', 'COPY DELETE POST PUT'.split(), 'current' ],
    ]
    print( getpaths( data, paths))

# vim:ts=4:sw=4:expandtab
