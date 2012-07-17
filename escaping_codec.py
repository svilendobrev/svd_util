#s.dobrev '2k4
'escape/unescape strings'

class Codec:
    _escaper = '\\'
    _encoding = {
        _escaper: '\\a',
        '\n': '\\n',
        '\t': '\\t',
        '\r': '\\r',
    }
    def __init__( me, encoding =_encoding, escaper =_escaper ):
        assert escaper in encoding
        me.escaper = escaper
        me.encoding = encoding  #dont change it!    #or .copy()  just in case

        import re
        rf = '(' + '|'.join( [ re.escape(e) for e in encoding ] ) + ')'
        me.rf = re.compile( rf )

        decoding = {}
        for k,v in encoding.iteritems(): decoding[v] = k
        me.decoding = decoding

        rb = '(' + '|'.join( [ re.escape(e) for e in decoding ] ) + ')'
        me.rb = re.compile( rb )


    if 0:   #using string.replace
        def encode( me, s):
            ' escape chars like \n, | '
            escaper = me.escaper
            encoding = me.encoding
            s = s.replace( escaper, encoding[ escaper ])     #first
            for k,v in encoding.iteritems():
                if k != escaper:
                    s = s.replace(k,v)
            return s
        def decode( me, s):
            ' unescape back chars like like \n, | '
            escaper = me.escaper
            encoding = me.encoding
            for k,v in encoding.iteritems():
                if k != escaper:
                    s = s.replace(v,k)
            s = s.replace( encoding[ escaper ], escaper)     #last
            return s

    else:   #using re.sub
        #def replacer_f( match): return me.encoding[ match.group(0) ]
        #def replacer_b( match): return me.decoding[ match.group(0) ]
            #lambda should be faster for big things - no getattr( me.encoding) inside
        def encode( me, s): return me.rf.sub( lambda match: me.encoding[ match.group(0) ], s)
        def decode( me, s): return me.rb.sub( lambda match: me.decoding[ match.group(0) ], s)



if __name__=='__main__':

    escaper = '\\'
    encoding = {
        escaper: '\\a',
        '\n': '\\n',
        '\r': '\\r',
        #'\032': '\\z',    #ctrl-z?
        '|' : '\\p',
    }

    codec = Codec( encoding, escaper)
    encode = codec.encode
    decode = codec.decode

    verbose = 0
    import sys
    for a in sys.argv[1:]:
        e = encode(a)
        d = decode(e)
        _verbose = verbose or d != a
        if _verbose: print repr(a),
        if _verbose: print '->', repr(e)
        if _verbose: print repr(d), '<-'
        if d != a:
            print '!!!error!'

    #enc.py `cat enc.py`    - space-delimited words by word
    #enc.py "`cat enc.py`"  - whole file at once
# vim:ts=4:sw=4:expandtab

