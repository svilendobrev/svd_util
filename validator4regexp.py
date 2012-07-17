#sdobrev 2004
'validator using regexps'

import re
class Validator4regexp:
    def __init__( me, regexp, description ='regexp', strip_regexp =None, ):
        descr = description
        if isinstance( regexp, str):
            regexp = re.compile( regexp)
            if not description: descr = regexp
        me.regexp = regexp.match

        if strip_regexp:
            if isinstance( strip_regexp, str):
                strip_regexp = re.compile( strip_regexp)
                if not description: descr += ','+strip_regexp
        me.strip_regexp = strip_regexp

        me.description = descr

    def __call__( me, v, **kargs_ignore):
        if not me.regexp( v):
            raise ValueError, 'wrong value %r, does not match %r' % (v, me.description)
        strip_regexp = me.strip_regexp
        if strip_regexp:
            v = strip_regexp.sub( '', v)     #remove them
        return v

_hex = '0-9a-fA-F'
validator_hex_pure    = Validator4regexp( '^[%s]+$'   % _hex,   'hex digits' )
validator_hex_pure0x  = Validator4regexp( '^0x[%s]+$' % _hex,   '0x, hex digits' )
validator_hex_space   = Validator4regexp( '^[%s][%s ]*$'   % (_hex, _hex), 'hex digits+space', strip_regexp=' ' )
validator_hex_space0x = Validator4regexp( '^0x[%s][%s ]*$' % (_hex, _hex), '0x, hex digits+space', strip_regexp=' ' )
validator_dec_pure    = Validator4regexp( '^\d+$',     'decimal digits' )
validator_dec_space   = Validator4regexp( '^[\d ]+$',  'decimal digits+space', strip_regexp=' ' )

if __name__ == '__main__':
    v = validator_hex_space

    v_ok = {
        '1234aF': '1234aF',
        '12 bc 78': '12bc78',
    }
    v_err = [
        '1234aFy',
        '0x122',
    ]
    for vin,vout in v_ok.iteritems():
        assert v( vin) == vout

    for vin in v_err:
        try:
            v( vin)
        except ValueError, e:
            print 'OK -', e
        else:
            raise ValueError, 'value %r must raise in %s' % (vin,v)
    print 'OK'

# vim:ts=4:sw=4:expandtab
