#!/usr/bin/env python
#svd'2k2-7
'better view onto python profiler results'
#XXX BEWARE That 2.4 - 2.5 - 2.6 have diff.file-format
try:
    from svd_util import optz
except:
    import os.path, sys
    p = os.path.realpath( __file__).split('/')
    sys.path.insert( 0, '/'.join( p[:-2]) )
    import optz #hope it lives in ..

optz.help( '%prog [options] [numberlines] infile')

optz.bool( 'hotshot',   help= 'load data as hotshot')
optz.text( 'strip',     help= 'regexp to strip from filenames; replaced with .#')
optz.text( 'rootstrip', default= '.*/(site-packages|python\d\.\d+)/',
    help= 'regexp to strip from filenames; replaced with ##; defaults to %defaults', )
optz.bool( 'withcalls', help= 'include call-stacks')
options,args = optz.get()

import re
import pstats
def func_strip_path(func_name):
    filename, line, name = func_name
    if options.rootstrip:
        filename = re.sub( options.rootstrip, '##', filename)
    if options.strip:
        filename = re.sub( options.strip, '.#', filename)
    return filename, line, name
    return func_name
    #return os.path.basename(filename), line, name
pstats.func_strip_path = func_strip_path
Stats = pstats.Stats

class mystats( Stats ):
    def __init__( self, *args ):
        self.withcalls = 0
        Stats.__init__( self, *args )

    def print_title(self):
        print('  %', end=' ')
        Stats.print_title( self)
    def print_line(self, func):  # hack : should print percentages
        cc, nc, tt, ct, call_dict= self.stats[func]
        print('%2d%%' % (100*tt/self.total_tt), end=' ')
        Stats.print_line( self, func )
        if not self.withcalls: return
        name_size = 12 #9+8+8+8+8 +5 +1
        if not call_dict:
            print("--")
            return
        clist = list(call_dict.keys())
        clist.sort()
        indent = " "*name_size
        for func in clist:
            name = pstats.func_std_string(func)
            print(indent + name + '('+ repr(call_dict[func])+')')
#            print pstats.f8(self.stats[func][3])
pstats.Stats = mystats

if options.hotshot:
    from hotshot.stats import load as mystats


#p = pstats.Stats( '_profile')
#p.sort_stats(1).print_stats(20)

wc=0
n =15

pargs = []
if not args:
    pargs = ["_profile"]
else:
    for a in args:
        if re.match( r'^\d+$',a):
            n=int(a)
        else:
            pargs.append(a)

p = mystats( *pargs )
p.withcalls = options.withcalls
p.strip_dirs().sort_stats( 1).print_stats( n)

# vim:ts=4:sw=4:expandtab
