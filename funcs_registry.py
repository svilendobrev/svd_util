#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
'''
support of functions with default and overridable kind=error/warning/off and args
'''

#machinery for management

class _kind:
    warning = 'warning'
    error   = 'error'

import inspect
import functools

class FuncsRegistry( dict):
    #name:func - all funcs in their default state/setup
    def _add( me, k, f):
        assert k not in me, 'func %r replaces already existing %r' % ( f, me[k] )
        me[k] = f
        spec = inspect.getargspec( f)
        defaults = dict( zip( *[reversed(a) for a in ( spec.args, spec.defaults or ())] ))
        f.defaults = defaults

    def warning( me, f):
        'decorator to add a func as warning (by-default)'
        f.kind = _kind.warning
        me._add( f.__name__, f)
        return f
    def error( me, f):
        'decorator to add a func as error (by-default)'
        f.kind = _kind.error
        me._add( f.__name__, f)
        return f

    def add_from_klas( me, klas):
        'take only localy declared func/methods from klas'
        for k,f in klas.__dict__.items():
            if not callable(f): continue
            me._add( k,f)
            f.kind = klas._kind

    def all( me):
        'default set'
        for k,f in sorted( me.items()):
            yield f #print( f.__name__, defaults, f.__doc__)


    def override( me, err, warn, debug= print, **map_func_to_args):
        ''' override the default set of funcs (off/args/kind=err/warn)
        one or more of named-args like:
        funcname = dict( .. arg1=v1, ..)   - override default args
        funcname = None - means disable
        funcname = dict( _kind= 'warning', ..) - override default kind
                one of 'error' or 'warning' or ''/None - empty means disable
        '''
        r = {}

        for k,v in map_func_to_args.items():
            if k not in me:
                err( 'unknown func requested: '+k)
                continue

        for k,f in me.items():
            if k not in map_func_to_args:
                r[k] = f
                continue

            v = map_func_to_args[ k]
            if v is None:
                debug( 'disable', k)
                continue      #skip


            assert isinstance( v, dict)

            v = v.copy()
            kind = f.kind
            if '_kind' in v:
                _kind = v.pop( '_kind', None)

                if not _kind:
                    debug( 'disable', k)
                    continue      #skip

                if _kind not in (warnings._kind, errors._kind):
                    warn( 'func %(k)s: ignoring unknown _kind %(_kind)r' % locals() )
                else:
                    kind = _kind

            unknown_args = set( v) - set( f.defaults)
            if unknown_args:
                err( 'func '+k + ': unknown args: ' + ','.join( sorted( unknown_args)))
                debug( 'err in func', k, '- disabling')
                continue

            if 1: #v:   #always
                fp = functools.partial( f, **v)
                fp.defaults = dict( f.defaults)
                fp.defaults.update( v)
                fp.kind = kind
                fp.__name__ = f.__name__
                fp.__doc__ = f.__doc__
                f = fp
            r[k] = f

        return r

    #print( f.__name__, f.kind, f.defaults, f.__doc__)
    @staticmethod
    def print( f, PFX =''):
        print( PFX, f.__name__, f.kind, f.defaults)
        if f.__doc__: print( PFX+'    ', f.__doc__.strip())

if __name__ == '__main__':
    messages = FuncsRegistry()

    class errors:
        _kind = 'error'

        def e1():
            'doc1'
        def e2():
            'doc2'
        def e3():
            'doc 3'

    class warnings:
        _kind = 'warning'

        def w1():
            '''help w1'''
        def w2( level =10):
            '''help w2
                multiline
            '''
        def w3( x =50):
            '''help w3
                multiline too
            '''

    messages.add_from_klas( warnings)
    messages.add_from_klas( errors)


    print( '======= list')
    for f in messages.all(): messages.print( f)

    print( '======= override')
    r = {}
    for k,f in sorted( messages.override(
            err = lambda *x: print( 'E',*x),
            warn= lambda *x: print( 'W',*x),
            w3 = dict( x=3, _kind= errors._kind ),
            e2= dict( trakla=2 ),
            e3= None,
            w4 = dict( level=3 ),
        ).items()):
            print( k, f.kind, f.defaults, f) #,f.__name__)
            r[k] = f
    assert 'w4' not in r
    assert 'e3' not in r
    assert 'e2' not in r
    assert r['w3'].kind == errors._kind
    assert r['w3'].kind != messages['w3'].kind
    assert r['w3'].defaults[ 'x'] == 3
    assert r['w3'].defaults[ 'x'] != messages[ 'w3'].defaults[ 'x']
    assert r['w2'].defaults == messages['w2'].defaults

# vim:ts=4:sw=4:expandtab
