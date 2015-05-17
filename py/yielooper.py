#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

class looper( object):
    '''
    wrapping looper for generators to allow usual usage of "for a in gen" AND send/throw into gen
    usage:

        def gen( n, ofs =0):        #some generator
            for a in range( n):
                ofs = yield a + ofs
                print( 'ofs', ofs)
                ofs = ofs or 0
        #...
        g = looper( gen(5))
        for a in g:
            print(a)
            #...
            if a ==2 :
                g.sent = 100
                continue
            #...
    '''
    def __init__( me, gen):
        me.gen = gen
        me.sent = None
        me.throw= None
    def __next__( me):
        if me.throw is not None:
            t, me.throw = me.throw, None
            r = me.gen.throw( t)  #not tested
        else:
            s, me.sent = me.sent, None
            r = me.gen.send( s)
        return r
    def __iter__(me): return me
    next = __next__     #py 2


if __name__ == "__main__":

    exp = '''
0
ofs None
1
ofs None
2
ofs 100
103
ofs None
4
ofs None
'''

    def gen( n, ofs =0):
        for a in range( n):
            ofs = yield a + ofs
            print( 'ofs', ofs)
            ofs = ofs or 0

    def t_correct_but_use_while():
    #    print( '100% correct but tedious')

        g5 = gen(5)
        send = None
        while True:
            try:
                a = g5.send(send)
            except StopIteration: break
            #...
            print(a)
            if a ==2 :
                send = 100
                continue
            #...
            send = None

    def t_use_for_but_static_attr_of_gen_func():
    #    print( 'using modified gen-func with static attr')
        def gen( n, ofs =0):
            for a in range( n):
                yield a + ofs
                ofs = getattr( gen, 'sent', None)
                gen.sent = None
                print( 'ofs', ofs)
                ofs = ofs or 0

        for a in gen(5):
            #...
            print(a)
            if a ==2 :
                gen.sent = 100
                continue
            #...

    def t_use_for_with_wrapper_and_usual_gen_func():
    #    print( 'using wrapping looper')

        g = looper( gen(5))
        for a in g:
            #...
            print(a)
            if a ==2 :
                g.sent = 100
                continue
            #...

    for f in [ f for k,f in sorted(locals().items()) if callable(f) and k.startswith('t_') ]:
        f.__doc__ = '>>> '+f.__name__+'()'+exp
        #f()
    import doctest
    doctest.testmod( verbose=True)

# vim:ts=4:sw=4:expandtab
