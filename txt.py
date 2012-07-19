#sdobrev 2005
'text encodings, escaping, whitespace stripping'

MODEL_ENCODING = 'utf-8'
PREFERRED_ENCODING = 'cp1251'
# which is which bitch?

def TXT( txt):  #to unicode.
    if isinstance(txt, unicode):
        return txt
    try:
        return unicode( txt, MODEL_ENCODING)
    except UnicodeDecodeError:
        return unicode( txt, PREFERRED_ENCODING)

def TXTL( lst):
    return [ TXT(i) for i in lst ]

_ = TXT

def u2s( value):
    if isinstance(value, unicode):
        value = value.encode('utf-8')
    return value

def XTX( txt):  #from unicode
    assert isinstance(txt, unicode)
    try:
        return txt.encode( PREFERRED_ENCODING)
    except UnicodeDecodeError:
        return txt.encode( MODEL_ENCODING)

#############

from xml.sax.saxutils import escape #, quoteattr

def escape_xml_attrs( kv_tuples):
    for k,v in kv_tuples:
        if isinstance(v,basestring):
            v = escape_xml_attr(v)
        yield k,v
def escape_xml_text( t):  return escape(t)
_escs = {'\n': '&#10;', '\r': '&#13;', '\t':'&#9;', '"': "&quot;" }
def escape_xml_attr( text): return escape( text, _escs)

###############

import re
whitespace = '\n\r \t\xa0'
def strip(x): return x.strip( whitespace)

re_spc = re.compile( '['+whitespace+']+')
def slim1( x): return re_spc.sub( ' ', x)
def slim( x): return strip( slim1( x) )

# vim:ts=4:sw=4:expandtab
