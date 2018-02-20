#sdobrev 2005
'various html escapers'

from . import escaping_codec
_escaper = '&'
_encoding = {
    _escaper: '&amp;',
    '<': '&lt;',
    '>': '&gt;',
}
htmlcodec = escaping_codec.Codec( _encoding, _escaper)


def lf2br(v):
    """turn linebreaks into <br>+linebreak"""
    return v.replace( '\n', '<br>\n' )

def wrap_pre(v):
    return '<pre>'+v+'</pre>'

_lf_escaped = _escaper+'#x0A;'
def escape_lf( v):
    """ turn linebreaks into escaped-linebreak - to be able to diff
        between linebreak in text and and linebreak in html-structure.
        text does not really need to be unescape_lf'ed back, except for readability
    """
    return v.replace( '\n', _lf_escaped )
def unescape_lf( v):
    return v.replace( _lf_escaped, '\n' )

# vim:ts=4:sw=4:expandtab
