#sdobrev 2008
'some usable default timezone implementation'

import datetime
tdZERO = datetime.timedelta(0)

def timedelta2neg_h_m( td):
    if td < tdZERO:
        neg = True
        td = -td
    else:
        neg = False
    s = td.seconds
    h = s//3600
    m = (s%3600)//60
    assert not s%60
    return neg,h,m

def strdelta( td):
    neg,h,m = timedelta2neg_h_m( td)
    return (neg and '-' or '+')+str(h)+':'+str(m)

import re

class TimezoneConst( datetime.tzinfo):
    #GMT [+-] Hours+ {: Minutes+}
    re_tz  = re.compile( 'GMT *((?P<sign>[+-]) *(?P<hours>\d+) *(: *(?P<minutes>\d+))?)?')
    def __init__( me, txt):
        me.delta = tdZERO
        m = me.re_tz.search( txt)
        if not m: return
        negative = m.group( 'sign') == '-'
        hours    = int( m.group('hours') or 0)
        assert 0<= hours <=23
        minutes  = m.group( 'minutes') or 0
        minutes = int( minutes)
        if minutes: assert 0<= minutes <=59
        me.delta = datetime.timedelta( hours= hours, minutes= minutes)
        if negative: me.delta = -me.delta

    def __str__( me):
        r = 'GMT'
        d = me.delta
        if not d: return r
        neg,h,m = timedelta2neg_h_m( d)
        return r + (neg and '-' or '+') + str(h) + (m and ':%02d' % m or '')

    def utcoffset( me, dt): return me.delta
    def tzname( me, dt): return str(me)
    def dst( me, dt): return tdZERO


def timestamp_tz_shift( t, tz1, tz2):
    'not tested; FORMAT_ISO8601 doesnt support timezone'
    from datetimez import FORMAT_ISO8601, datetime2timestamp
    dt = FORMAT_ISO8601.mkdatetime( t) #gmt=utc
    dtz1 = dt.replace( tzinfo=tz1)
    dtz2 = dtz1.astimezone( tz2)
    return datetime2timestamp( dtz2)    #as if gmt=utc

'''options:
    - make&keep timestamp GMT, shift only date/hour/weekdays
    - shift timestamp too as ??? why
'''

GMT = UTC = TimezoneConst( 'GMT')

# vim:ts=4:sw=4:expandtab
