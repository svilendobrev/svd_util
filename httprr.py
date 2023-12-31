import urllib.request, urllib.parse, urllib.error
#from http import HTTPStatus    # int-enum
import json as _json

#  ~/src/bin/util/./ext/multipart_httppost.py
import mimetypes, io, uuid
def multipart_encode( fields, files, boundary = None, buf = None):
    if boundary is None:
        #boundary = mimetools.choose_boundary()
        #boundary = binascii.hexlify(os.urandom(16)).decode('ascii')
        boundary = uuid.uuid4().hex
    bound = '--'+str(boundary)
    r = []
    line = r.append
    for key, value in fields:
        line( bound)
        line( 'Content-Disposition: form-data; name="%s"' % key)
        line('')
        line( str(value))
    for key, fd in files:
        filename = fd.name.split('/')[-1]
        contenttype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        line( bound)
        line( 'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename) )
        line( 'Content-Type: %s' % contenttype )
        #file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
        # line( 'Content-Length: %s' % file_size )
        line('')
        fd.seek(0)
        line( fd.read() )
    line( bound+ '--')
    line('')

    NL = '\r\n'.encode('ascii')
    if buf is None: buf = io.BytesIO()    #cStringIO.StringIO()
    for l in r:
        if not isinstance( l, bytes):  l = l.encode('utf-8')
        buf.write( l+NL)
    buf = buf.getvalue()
    return boundary, buf

def multipart_req_data_ctype( datadict):
    file = io.IOBase
    v_files = [ (k,v) for k,v in datadict.items() if isinstance( v, file) ]
    if not v_files: return
    v_fields= [ (k,v) for k,v in datadict.items() if not isinstance( v, file) ]
    boundary, data = multipart_encode( v_fields, v_files)
    contenttype = f'multipart/form-data; boundary={boundary}'
    return data, contenttype

def request( url, datadict =None, json =False, headers ={}, debug =False):
    'only creates req, no sending'
    #method = 'GET' if datadict is None else 'POST'
    data = None
    if isinstance( datadict, dict): #data is not None and not isinstance( data, basestring):
        if json:
            data = _json.dumps( datadict ).encode( 'utf-8')
            headers = { 'content-type': 'application/json', **headers}  #'authorization': f'token {sometoken}') }
            #TODO 'content-type': 'application/json ; charset=utf-8' XXX ??
        else:
            multipart = multipart_req_data_ctype( datadict)
            if not multipart:
                data = urllib.parse.urlencode( datadict)
                data = data.encode( 'ascii')
            else:
                data, contenttype = multipart
                headers = { 'content-type': contenttype, **headers}  #'authorization': f'token {sometoken}') }

    # Request: if data: method='POST' ; headers = dict( Content-Type: application/x-www-form-urlencoded  ) ; else: GET
    req = urllib.request.Request( url, data, headers= headers)
    if debug:
        print( '\n>>>> req:', dict( url= req.get_full_url(), method= req.get_method(), headers= req.header_items(), data= req.data))
    return req

if 'fix fresp':
    def respinfo( fresp):
        if not hasattr( fresp, 'status'):   #pre 3.9
            fresp.headers   = fresp.info()
            fresp.status    = fresp.code
        return dict( status= fresp.status, headers= str( fresp.headers) )
else:  #readonly:
    def respinfo( fresp):
        if hasattr( fresp, 'status'):   #3.9+
            return dict( status= fresp.status, headers= str( fresp.headers) )
        return dict( status= fresp.code, headers= str( fresp.info()) )  #pre 3.9

def hack_verbose_HTTPError():
    urllib.error.HTTPError.__str__ = lambda err: f'''\
HTTP Error {err.code}: {err.msg}
 url: {getattr( err, 'filename', None)}
 data: {err.read()}'''
# headers: {getattr( err, 'headers', None)}

def response( req, debug =False):
    '''send req, read-all, return dict( status, headers, data) or raise
        headers is dictlike, ignores case of header-names - doc/python3/html/library/email.message.html#email.message.EmailMessage
    '''
    try:
        with urllib.request.urlopen( req) as f:      #default: method='POST' ; headers = dict(  Content-Type: application/x-www-form-urlencoded  )
            if debug and debug > 1: print( ' <<< resp:', respinfo( f))
            elif debug: print( ' <<< resp: status=', respinfo( f)['status'])
            data = f.read()    #.decode( 'utf-8') XXX
            if debug > 1: print( ' <<< resp-read:', respinfo( f))
            if debug: print( ' <<< resp-data:', data)
            return dict( url= f.url, status= f.status, headers= f.headers, data= data)
    except urllib.error.HTTPError as err:
        if debug: print( f'''\
!! resp-Error: {err}
 url:  {getattr( err, 'filename', None)}
 code: {getattr( err, 'code', None)}
 headers: {getattr( err, 'headers', None)}
 data:
''', err.read() )
        raise

def req_resp( url, datadict =None, json =False, headers ={}, debug =False):
    return response( request( url, datadict, json= json, headers= headers, debug= debug), debug=debug)

def json_resp( resp):
    'reads+assigns resp.json if content-type is json  ---  no decoding !'

    if 'application/json' in resp['headers'].get( 'content-type', '').lower():   # headers ignores case of header-names
        resp['json'] = _json.loads( resp['data'])   #.decode( 'utf-8') ?? XXX
    return resp

def data_utf8( resp):
    return resp['data'].decode( 'utf8')
def exc_utf8( exc):
    return exc.read().decode( 'utf8')

# vim:ts=4:sw=4:expandtab
