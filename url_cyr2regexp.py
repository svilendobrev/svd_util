#!/usr/bin/env python
#sdobrev 2010
'cyrillic in urls - multi-transcriptions, 1251/utf, ignorecase, etc'

from __future__ import print_function
#ok for py3 and py2
import sys
v3 = sys.version_info[0]>=3

def reor( xx):
    if xx[0]=='^':
        assert not xx.isalpha()
        return '['+xx+']'
    return '(' + '|'.join( xx ) + ')'

import re
re_brackets = re.compile( '\[ ([^[]+) \]', re.VERBOSE)
def brepl( m):
    return reor( m.group(1) )

def c2lcuc( a):
    r = []
    a = re_brackets.sub( brepl, a)
    for c in a:
        lc = c.lower()
        uc = c.upper()
        r.append( lc != uc and [lc,uc] or lc )
    return r

if v3:
    def hx(x): return repr(x)[2:-1]   #b'...'
else:
    hx = repr

def reg( a, enc ='utf8', spc ='', do_optz_partial =True):
    r = []
    for rc in c2lcuc(a):
        if isinstance( rc, (list, tuple)):
            lc,uc = rc
            #print lc,uc
            l,u = (x.encode( enc) for x in (lc,uc))
            if do_optz_partial:
                if v3: same = bytes()
                else: same = ''
                diff = []
                for i in range(min(len(l),len(u))):
                    if l[i] == u[i]:
                        same += l[i:i+1]    #bytes[i] -> int, bytes += int -> error
                    else:
                        diff = l[i:], u[i:]
                        break
                if diff:
                    br = len(diff[0])==len(diff[1])==1 and '[ ]' or '(|)'
                    rdiff = br[0] + br[1].strip().join( hx(x) for x in diff) + br[-1]
                #print same, diff
                rc = (hx(same)+rdiff).replace("'",'')
            else:
                rc = reor( [hx(l), hx(u)] )

        #print c, rc
        r.append(rc)
    #print enc,a,
    return spc.join( r)

def rule1( target, regexp ):
    regexp = ''.join( regexp.split())
    if '$' in target:
        rfl = ''
        grupa = ''
    else:
        target += '/'
        rfl,nfl = '($|/(.*))', 2    #target/$x
        #rfl,nfl = '($|/.*)',   1   #target$x
        grupa = regexp.count('(')+nfl
        assert grupa<=9
        if grupa: grupa = '$'+str(grupa)
    return '''
RewriteRule ^%(regexp)s%(rfl)s  %(target)s%(grupa)s [NC,R=301]
'''.strip() % locals()

def rule( target, lat, cyr='', pfxs =(), cond= True, cyr_is_reg =False, encs= ['utf8'], **kignore):
    if pfxs:
        pfxs = [ p.strip().rstrip('/') for p in pfxs ]
        pfxs = [ p and p+'/' for p in pfxs ]
        if len(pfxs)>1: pfxs = reor( pfxs)
        else: pfxs = pfxs[0]
    else: pfxs = ''

    if lat:
        yield ' '.join( ('#', lat, pfxs))
        if cond:
            tt = re.sub( '\$\d', '.*', target )
            yield '''
RewriteCond %%{REQUEST_URI} !^%(tt)s'''.strip() % locals()
        yield rule1( target, pfxs+lat)
    if cyr:
        yield ' '.join( ['#', cyr, pfxs] + encs)
        for e in encs:
            rcyr = cyr_is_reg and cyr or reg( cyr, enc=e)#, do_optz_partial =False)
            yield rule1( target, pfxs+rcyr)
    yield ''

if __name__ == '__main__':
    import sys
    try: spc = sys.argv.remove( '--spc') or ' '
    except: spc=''

    from util import eutf
    eutf.fix_std_encoding()
    for a in sys.argv[1:]:
        a = a.decode( eutf.e_utf_stdout() and 'utf8' or 'cp1251')
        #print a
        for enc in ('utf8', 'cp1251'):
            print( enc, a)
            print( reg( a, enc, spc))

#rules-usage
#for a in rule( '/detski/lego',   'lego',     'лего',     pfxs= ['', 'detski'] ): print a

# vim:ts=4:sw=4:expandtab
