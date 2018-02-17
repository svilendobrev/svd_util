#s.dobrev 2k3-4
'symmetrical url-to/from-dict conversions'

try:
    from urllib import unquote, quote, unquote_plus
except:
    from urllib.parse import unquote, quote, unquote_plus

#urllib.parse.parse_qs parse_qsl
def query2dict( query, dict= dict, unquote =unquote, unquote_value =unquote_plus):
    querymap = dict()
    if query:
        for q in query.split( '&' ):
            try:
                key,value = q.split( '=', 1)
            except ValueError:
                key = q; value = None
            #always unquote after split!
            if unquote:
                if key:   key   = unquote( key)
                if value: value = unquote_value( value)
            querymap[ key] = value
    return querymap

#urllib.parse.urlencode
def dict2query( querymap, quote =quote, amp ='&', equ ='=' ):
    r = ''
    dlm = ''
    for item in querymap.iteritems():
        r+= dlm
        if item[1] is None:
            item = item[:1]
        if quote: item = [ quote(m) for m in item ]
        r+= equ.join( item)
        dlm = amp
    return r


if 0:
    from urlparse import urlparse as _urlparse
    def urlparse( uri):
        return _urlparse( uri)[2:]    #ignore scheme,netloc
else:
    #from medusa.http_server.http_request
    import re
    # <path>;<params>?<query>#<fragment>
    _path_regex_match = re.compile( r'([^;?#]*)(;[^?#]*)?(\?[^#]*)?(#.*)?' ).match

    def urlparse( uri):
        m = _path_regex_match( uri)
        if not m or m.end() != len(uri):
            raise ValueError( "Broken URI")
        else:
            return m.groups()

# vim:ts=4:sw=4:expandtab
