# sdobrev 2004
'around generating code - C,python,vim'
from __future__ import print_function

_CVShead = '$I' + 'd$\n'   #separated!
_VIMtail = ' v' + 'im:ts=4:sw=4:expandtab\n' #separated!
CVShead = '//'+_CVShead
VIMtail = '//'+_VIMtail
CVShead_py = '#'+_CVShead
VIMtail_py = '#'+_VIMtail

def vimtail2line( items):    #e.g. dict/order
    return ':'.join( (     v is True  and k
                        or v is False and 'no'+k
                        or k+'='+str(v)
                    ) for k,v in items )
def vimtail2items( line):   #stripped of #//comments
    #line = line.lstrip('# ')
    if not line.startswith('vim:'): return
    vims = [ kv.split('=') for kv in line.split(':') ]
    return [ (len(kv) == 2 and kv or (k,True)) for kv in vims ]

_AUTOGEN_STAMP = """\
 %(filename)s: automaticaly generated file
"""
AUTOGEN_STAMP = '//'+_AUTOGEN_STAMP
AUTOGEN_STAMP_py = '#'+_AUTOGEN_STAMP

def indent( s, ntabs =1):
    return s.replace( '\n', '\n'+' '*4*ntabs )
def comment( s):
    return s.replace( '\n', '\n//')

def H_WRAP( H_name, txt):
    return """\
#ifndef %(H_name)s
#define %(H_name)s

%(txt)s

#endif  //%(H_name)s
""" % locals()

def _commentable_include( name, commentable =True):
    if commentable and name.startswith('#'): return '//',name[1:]
    return '', name

def includes( all =(), commentable =True ):
    return [ '%s#include "%s"' % _commentable_include( inc, commentable) for inc in all ]

def usings( all = () ):
    return [ 'using %(use)s;' % locals() for use in all ]

def pathname2identifier( name):
    return name.replace( '/', '_' ).replace( '.', '_' )

def rstrip_lines( txt):
    txt = txt.replace( '  \n', '\n' )
    txt = txt.replace( '  \n', '\n' )
    txt = txt.replace( ' \n', '\n' )
    txt = txt.replace( ' \n', '\n' )
    return txt

def is_comments_only( txt):
    for line in txt.split( '\n'):
        line = line.strip()
        if line and not line.startswith('//'):
            return False
    return True

def save_if_different( filename, txt, makedirs =True, print_at_write =print ):
    if makedirs:
        import os.path
        fpath = os.path.dirname( filename)
        if fpath and not os.path.exists( fpath):
            os.makedirs( fpath )
    try:
        old = file( filename).read()
    except IOError:
        old = None
    if txt != old:
        if print_at_write: print_at_write( filename)
        file( filename, 'w').write( txt )
        return True

# vim:ts=4:sw=4:expandtab
