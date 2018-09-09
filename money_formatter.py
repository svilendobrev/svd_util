#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function #,unicode_literals
# ?2008
'text-format amount of money'

from decimal import Decimal

def moneyfmt( value, places=2, currency='', sep='', decimal_point='.', pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:     required number of places after the decimal point
    currency:   optional currency symbol after the sign
    sep:        optional grouping (thousands) separator, i.e. comma, period, space, blank..
    decimal_pt: decimal point indicator (comma, period, whatever)
                only specify as blank when places is zero
    pos:        optional sign for positive numbers, e.g. '+'
    neg:        optional sign for negative numbers, e.g. '-', '('
    trailneg:   optional trailing negative indicator, e.g. '-', ')'

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt( d, currency='$', sep=',')
    '-$1,234,567.89'
    >>> moneyfmt( d, places=0, sep='.', decimal_point='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt( d, currency='$', sep=',', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt( 123456789, sep=' ')
    '123 456 789.00'
    >>> moneyfmt( 123456789, places=0, sep=' ')
    '123 456 789.'
    >>> moneyfmt( 123456789, places=0, sep=' ', decimal_point='')
    '123 456 789'
    >>> moneyfmt( Decimal('-0.02'), neg='<b>', trailneg='</b>')
    '<b>0.02</b>'

    """
    value = Decimal( value)
    q = Decimal((0, (1,), -places))    # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    assert exp == -places

    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop

    if sign:
        build( trailneg)
    for i in range( places):
        build( next() if digits else '0')

    build( decimal_point)

    i = 0
    while digits:
        build( next())
        i += 1
        if i == 3 and digits:
            i = 0
            build( sep)

    if result[-1] is decimal_point:
        build('0')

    build( currency)
    build( neg if sign else pos)

    result.reverse()
    return ''.join(result)

if __name__ == '__main__':
    import sys
    print(moneyfmt( sys.argv[1]))

# vim:ts=4:sw=4:expandtab
