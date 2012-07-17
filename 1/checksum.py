#s.dobrev 2k4
''' checksummers:
all these are factories which produce functions to calculate
checksum over the input data (single str or iter[ str] ),
and return it as-is or as hexstr.
    use:
        chksumfunc = <checksumer_factory_type>( out_hex =True, in_iter =False)
    combination matrix:
        output      input           type
        (hex/raw) x (iter/single) x (md5/sha/crc32)
'''


def _make_checksumer_hasher( mod, out_hex =True, in_iter =False ):
    ctor = mod.new
    if in_iter:
        def from_iter( data):
            s = ctor()
            update = s.update
            for d in data: update( d)
            return s
        chk = from_iter
    else:
        chk = ctor

    if out_hex:
        m = lambda data: chk( data).hexdigest()
    else:
        m = lambda data: chk( data).digest()
    return m


def make_checksumer_md5( **k):
    """bytelen()==16/32"""
    import md5
    return _make_checksumer_hasher( md5, **k)

def make_checksumer_sha( **k):
    """bytelen()==20/40"""
    import sha
    return _make_checksumer_hasher( sha, **k)


def make_checksumer_crc32( out_hex =True, in_iter =False ):
    """bytelen()==4/8"""

    from binascii import crc32, hexlify
    if in_iter:
        def from_iter( data, s0=''):
            update = crc32      #lookup binding once
            s = update( s0)
            for d in data:
                s = update( d,s)
            return s
        chk = from_iter
    else:
        chk = crc32

    if out_hex:
        from struct import pack
        m = lambda data: hexlify( pack( '>l', chk( data) ))
        #m = lambda data: _hexdigest4int( chk( data) )
    else:
        m = chk
    return m

if __name__=='__main__':

    from binascii import crc32, hexlify
    from struct import pack
    def _digest4int( s):
        return pack( '>l', s)
    def _hexdigest4int( s):
        #return hex(s)
        #return hex( (1L<<32) + s) [-9:-1]
        #return ('%x' % ( (1L<<32) + s)) [-8:]
        return hexlify( pack( '>l', s) )


    class checksum_crc32( object):
        __slots__ = [ 's' ]
        crc32 = None
        hexlify = None
        def __init__( me, data=''):
            me.s = me.crc32( data)
        def update( me, data):          #slow
            me.s = me.crc32( data, me.s)
        def digest( me):  return me.s
        def digest2( me): return _digest4int( me.s)
        def hexdigest( me): return _hexdigest4int( me.s)
        def __str__( me):
            return 'checksum_crc32:'+me.hexdigest()

        def from_iter( klas, data):
            m = klas()
            s = m.s
            crc32 = klas.crc32
            for d in data:
                s = crc32( d,s)
            m.s = s
            return m
        from_iter = classmethod( from_iter)

    checksum_crc32.crc32 = crc32
    chk1 = make_checksumer_crc32( in_iter=True)
    #chk2 = make_checksumer_crc32( in_iter=False)
    chk2 = checksum_crc32.from_iter
    import sys
    #f = file( len(sys.argv)>1 and sys.argv[1] or __file__, 'rb' )

    import itertools as it
    class F:
        def __iter__(me):
            return it.repeat( ' jkfldsa; fjdskl;f dskl', 1000000)
        def seek(*a): pass
    f = F()

    from time import clock as tm

    f.seek(0)
    t = tm()
    s = chk1( iter(f) )
    t = tm() - t
    print s, 'ok1', t
    f.seek(0)
    t = tm()
    s = chk2( iter(f) )
    t = tm() - t
    print s, 'ok2', t


    N = 12+0000
    chk0 = make_checksumer_crc32()
    t = tm()
    for a in xrange(N):
        s = chk0( '13u iouiouiopuiopio jko ' )
    t = tm() - t
    print 'factory, single', N, s, t

    t = tm()
    for a in xrange(N):
        sa = crc32( '13u iouiouiopuiopio jko ' )
        s = _hexdigest4int( sa)
    t = tm() - t
    print 'direct,  single', N, s, t

    # vim:ts=4:sw=4:expandtab
