#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import print_function
'guess utf or byte-encoding, and (on-the-fly) conversion, on text or files. python2 + python3'

import re
import sys
import codecs
_v3 = sys.version_info[0]>=3
if _v3:
    dd = b'[\xD0\xD1]'
    cc = b'[\x80-\xBF]'
    def e_utf( stream, nbytes =200, buffer =None):
        'look in first nbytes'
        peek = getattr( stream, 'peek', None)
        if not peek: peek = stream.buffer.peek
        r = peek( nbytes)
        return bgutf.search( r)
    def readlines( input, nonutf_enc= 'cp1251', debug =False):
        if not isinstance( input, str): #stream?
            _e_utf = e_utf( input)
            ienc = _e_utf and 'utf8' or nonutf_enc
            if debug: print( ienc)
            for a in codecs.getreader( ienc)( input.detach() ):
                yield a.rstrip()
            return
        fname = input
        _e_utf = e_utf( open( fname, 'r'))   #NOT t
        ienc = _e_utf and 'utf8' or nonutf_enc
        if debug: print( ienc)
        with open( fname, encoding=ienc) as f:
            for a in f:
                yield a.rstrip()

    #sys.stdout.buffer.write( b'abc')
    #sys.stdin = codecs.getreader("utf-8")(sys.stdin.detach())
    #def binary_stdio():
    #    sys.stdin = sys.stdin.detach()
    #    sys.stdout = sys.stdout.detach()
else:
    dd = '[\xD0\xD1]'
    cc = '[\x80-\xBF]'
    def e_utf( lines, nlines =10, buffer =None):
        'look in first nlines'
        for a in lines:
            if buffer is not None: buffer.append(a)
            if bgutf.search( a): return True
            nlines-=1
            if not nlines: break
        return False

    def readlines( lines, nonutf_enc= 'cp1251', debug =False):
        if isinstance( lines, str):
            lines = file( lines)
        buffer = []
        ienc = e_utf( lines, buffer= buffer) and 'utf8' or nonutf_enc
        if debug: print( ienc)
        for a in buffer:
            yield a.decode( ienc).rstrip()
        for a in lines:
            yield a.decode( ienc).rstrip()

xutf  = re.compile( dd)
bgutf = re.compile( dd+cc+dd+cc)

import sys,locale,os
def e_utf_stdout():
    #locale/stdout may fail on virtual terminals e.g. vim's output
    return 'utf' in ' '.join( [
                        locale.getpreferredencoding() or '',
                        sys.stdout.encoding or '',
                        os.environ.get( 'LANG', '')
                        ] ).lower()
    return 'utf' in (os.environ.get( 'LANG', '').lower() +' '+ sys.stdout.encoding)

if 0:   #for sitecustomize.py
    if sys.platform == 'win32':
        ENC = e_utf_stdout() and 'utf8' or 'cp1251'
        for name in 'stdout stderr'.split(): #,  stdin __stdin__
            f = getattr( sys, name)
            if f.encoding != ENC:
                import codecs
                fr,to = ENC,f.encoding
                #if 'in_' in name: fr,to=to,fr
                ef = codecs.EncodedFile( f, fr, to, errors='replace')
                setattr( sys, name, ef)
                #print name, id(f), id(ef), id(getattr( sys,name)), fr,to

if _v3:
    def filew( enc, f, mode=None, *a,**k):
        if isinstance( f, str): return open( f, mode= mode or 'w', encoding=enc, *a,**k)
        return codecs.getwriter( enc)( f, 'replace')
else:
    def filew( enc, f, mode=None, *a,**k):
        if isinstance( f, basestring): f = file( f, mode= mode or 'w', *a,**k)
        return codecs.getwriter( enc)( f, 'replace')
def filew_utf( *a,**k): return filew( 'utf-8', *a,**k)

def fix_std_encoding( stdout =True, stderr =True, ENC =None ):
    #XXX fails if repeated
    ENC = ENC or (e_utf_stdout() and 'utf8' or 'cp1251')
    if stdout is True: stdout = ENC
    if stderr is True: stderr = ENC
    for f in 'stdout stderr'.split():
        ENC = locals()[f]
        #print >>sys.stderr, f,ENC
        if not ENC: continue
        enc = getattr( sys, f).encoding
        #print f, enc
        #if not enc:
        if enc != ENC:
            o = getattr( sys, f)
            if _v3:
                o = o.detach()
            fw = filew( ENC, o)
            setattr( sys, f, fw )
            fw.encoding = ENC


if __name__ == '__main__':
    del sys.argv[0]
    try: sys.argv.remove('-t')
    except:
        fix_std_encoding()
        for fname in sys.argv:
            for a in readlines( fname):
                print( a) #.encode( oenc)
    else:
        for fname in sys.argv:
            print( fname,':', e_utf( open( fname, 'r')) and 'utf' or 'ne')

# vim:ts=4:sw=4:expandtab
