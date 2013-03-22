#!/usr/bin/env python
# -*- coding: utf-8 -*-

from couchdb import Server, Unauthorized
from couchdb import client, design

#other special views Server.:
# .config .stats .tasks .uuids
# XXX if server  -> does ping
# just server.resource.get_json()  also should give some info??

# _security obj has no id...

# class couchdb.Document is useless
from svd_util.struct import DictAttr
import couchdb
client.Document = couchdb.Document = DictAttr

#####################

if 1*'_replicator':
    client.SPECIAL_DB_NAMES.update( '_replicator'.split())
    def replicate( server, source, target, **options):
        'copy paste .. to use _replicator'
        data = {'source': source, 'target': target}
        data.update(options)
        status, headers, data = server.resource.post_json( '_replicator', data)
        return data
    Server.replicate = replicate

#####################

def session( server, username, password):
    '_session itself can also be used via cookie without name/password - to logout?'
    data = dict( name= username, password= password)
    status, headers, data = server.resource.post_json( '_session', data)
#    print( status, headers, data)
    if not data.get('ok'): return   #err
    name = data['name']
    if not name: return     #expired/logout
    assert name == username
    return status, headers, data

#####################

def delete( db, doc):
    """Delete the given document from the database.
    AND return the new rev!
    """
    if doc['_id'] is None:
        raise ValueError('document ID cannot be None')
    s,h,data = db.resource.delete_json(doc['_id'], rev=doc['_rev'])
    #print 1111111, s,h,data
    #doc['_rev'] =
    return data['rev']


#####################

if 1*'simplest':
    def get_cookie_direct( headers):
        return headers.get( 'Set-Cookie','').split(';')[0]

elif 0*'most-generic':
    #import cookielib
    #jj = cookielib.CookieJar()
    class _fake_resp:
        def __init__( me, h): me.h = h
        def info( me): return me.h
    def get_cookies_via_cookiejar( cookiejar, server, *a,**ka):
        from urllib2 import Request
        cookiejar.extract_cookies( _fake_resp( headers), Request( server.resource.url))

elif 0*'parse_ns':
    def get_cookies_via_parse( headers):
        return cookielib.parse_ns_headers( headers.headers)

if 10:
    get_cookie = get_cookie_direct
    from couchdb import http
    _Session = http.Session
    class Session( _Session):
        _cookie = None
        def request( me, *a,**ka):
            if me._cookie:
                headers = ka.get( 'headers')
                if not headers or 'Cookie' not in headers:
                    ka[ 'headers' ] = dict( headers or (), Cookie= me._cookie)
            status, headers, data = _Session.request( me, *a,**ka)
            me._cookie = get_cookie( headers)
            return status, headers, data
    http.Session = Session


from couchdb import json as _json
def put_json_always( resource, path =None, body =None):
    #XXX path in resource.put/_request is useless for _real_ paths
    if path:
        if isinstance( path, basestring): path = path.split('/')
        resource = s.resource( *path)
    body = _json.encode( body).encode('utf-8')
    return resource.put_json( body= body)

#####################

from couchdb import http
#Resource. def _request(self, method, path=None, body=None, headers=None, **params):
#Session. def request(self, method, url, body=None, headers=None, credentials=None, num_redirects=0):
_srequest = http.Session.request
def srequest( *a,**ka):
    try: return _srequest( *a,**ka)
    except Exception as e:
        e.request_args = a,ka
        raise
http.Session.request = srequest

#####################

if 0*'hack TemporaryView.options':  #XXX if empty SEQ_FIELDNAME below
    json = client.json
    def _exec(self, options):
        body = {'map': self.map_fun, 'language': self.language}

        if getattr( self, 'local_seq', None):
            body.update( options= {
                "local_seq" : True,
                #"include_design" : True
                })

        if self.reduce_fun:
            body['reduce'] = self.reduce_fun
        if 'keys' in options:
            options = options.copy()
            body['keys'] = options.pop('keys')
        content = json.encode(body).encode('utf-8')
        _, _, data = self.resource.post_json(body=content, headers={
            'Content-Type': 'application/json'
        }, **self._encode_options(options))
        return data
    client.TemporaryView._exec = _exec
    client.TemporaryView.local_seq = True

#####################

if 0:
#design.ViewDefinition:
    #XXX defect! h*ck! sort it stupid!
    @staticmethod
    def sync_many( db, views, **ka):
        return design.ViewDefinition.sync_many( db, sorted( views, key= design.attrgetter('design')), **ka)


if __name__ == '__main__':
    def test_session():
        import cu
        s = cu.Server( 'http://osha:5984')
        try:
            print s['czuha']
        except Unauthorized:
            print ' ok inaccessible'
        else:
            raise RuntimeError('accessible')
        cu.session( s, username='uha',password='uha')
        print s['czuha']

    test_session()

# vim:ts=4:sw=4:expandtab
