#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals
#sdobrev 2006-2009-
'time minutes-seconds-frames conversions/prettyprint'

def sec2minsec( s):
    neg = s<0
    if neg: s = -s
    m = int(s/60)
    ss = s-m*60
    if neg: m = -m
    return m,ss

def prnsec( sec):
    m,ss = sec2minsec(sec)
    return '%(m)2d:%(ss)04.1f' % locals()

def minsec2sec( msf):
    '[-][[hr:]min:]sec[.subsec]'
    neg = msf.startswith('-')
    if neg: msf = msf[1:]
    ms = msf.split(':')
    s = ms[-1]
    m = len(ms)>=2 and ms[-2] or 0
    h = len(ms)>=3 and ms[-3] or 0
    r = 60*60*int(h) + 60*int(m) + float(s)
    if neg: r = -r
    return r

def frame2minsec( args, FS =75):
    'whats this? FS=75 is CD-audio-frames'
    f0 = 0
    for a in args:
        f = int(a)
        f -= f0
        #if not f0: f0 = f  was this ???
        f0 = f
        s = int(f/FS)
        ff = f-s*FS
        m,ss = sec2minsec(s)
        yield '%d:%02d.%02d' % (m,ss,ff)

if __name__=='__main__':
    import sys
    if sys.argv[1:] and sys.argv[1].startswith('-fs'):
        FS = sys.argv[1].split('=')
        FS = len(FS)>1 and int( FS[1]) or 75
        for r in frame2minsec( sys.argv[2:] or sys.stdin, FS): print( r)
    else:
        for a in sys.argv[1:] or sys.stdin:
            print( minsec2sec( a) if ':' in a else prnsec( float(a)) )

# vim:ts=4:sw=4:expandtab
