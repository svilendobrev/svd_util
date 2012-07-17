#s.dobrev 2004-2007

"""
symmetric datetime conversions to/from text.
all this mess below because datetime.* HAS NO fromiso() or anything similar

 datetime2timestamp, timestamp2datetime - convert between UTC timestamp and datetime; usual time.mktime is localtime!
 class FORMAT_ISO8601: converters from ISO8601 to datetime, float, tuple; and other cosmetics
 class datetimez: stupid datetime with method from_ISO8601()
 class datetime, date, time: smart replacements for original datetime.* using regexps
    #can construct from text_ISO8601, another datetime.* or original args/kargs of datetime.*
    #can construct original datetime.*, or itself if _make_base=False
    #can change regexps - inherit and set _re=None in new class to force recalculation

"""

import datetime as _dt
import time as _time
import calendar as _calendar

def datetime2timestamp( dt, local =False):    #return float
    if local: return _time.mktime( dt.timetuple())
    return _calendar.timegm( dt.timetuple() )
def timestamp2datetime( t, local =False):
    if local: return _dt.datetime.fromtimestamp( t)
    return _dt.datetime.utcfromtimestamp( t)


class FORMAT_ISO8601:
    #_FORMAT_ISO8601 ='YYYY-MM-DDTHH:MM:SS'   #'.mmmmmm+HH:MM' #T=' '

    def change_format( delimiter, date ='%Y-%m-%d', time ='%H:%M:%S'):
        return date + delimiter + time   #'.mmmmmm+HH:MM' #T=' '
    delimiter = 'T'
    format = change_format( delimiter)
    #inherit, set delimiter, set format= thisklas.change_format( delimiter) or whatever

    change_format = staticmethod( change_format)

    @classmethod
    def str( klas, dt): return dt.strftime( me.format )

    @classmethod
    def nozone( klas,   timetext): return timetext.split('.',1)[0]     #ignore ...zone at end
    @classmethod
    def timeonly( klas, timetext): return timetext.split( klas.delimiter,1)[1]
    @classmethod
    def dateonly( klas, timetext): return timetext.split( klas.delimiter,1)[0]

    @classmethod
    def mktime_struct( klas, timetext):   #ret tuple
        #timetext = nozone( timetext)            #ignore .0Z at end
        return _time.strptime( timetext, klas.format )
    @classmethod
    def mktime( klas, timetext, local =False):  #ret float
        if local: return _time.mktime( mktime_struct( timetext))
        return _calendar.timegm( klas.mktime_struct( timetext))

    @classmethod
    def mkdatetime( klas, timestamp, local =False):  #ret datetime
        if isinstance( timestamp, basestring):
            return _dt.datetime.strptime( timestamp, klas.format )
            #return _dt.datetime( *mktime_struct( timestamp)[:6])
        return timestamp2datetime( timestamp, local=local)

#using strftime/strptime
#warning: this only has a converter text_ISO8601->datetime - but datetimez( text) does not work
#actualy doesnt have to be datetime
class datetimez( _dt.datetime):
    #ISO8601 ='YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM' #T=' '
    FORMAT = '%Y-%m-%d %H:%M:%S'    #part of the ISO8601
    def __str__( me): return me.strftime( me.FORMAT)
    @classmethod
    def from_ISO8601( klas, s):
        return klas.strptime( s, klas.FORMAT)
        #t = _time.strptime( s, datetimez.FORMAT)
        #return datetimez.fromtimestamp( _time.mktime(t) )

#using ISO8601/regexps
#this IS a class which produces either original datetime.*, or itself if _make_base=False
#can construct from text_ISO8601, another datetime.* or whatever other args/kargs of original datetime.* ctor

import re
args_date= 'year month day'.split()
args_time= 'hour minute second'.split()
args_datetime = args_date + args_time + [ 'microsecond' ]

class _dt_base( object):
    _make_base = True   #use False to tell __new__ to make klas and not base objects

    #ISO8601 ='YYYY-MM-DDTHH:MM:SS.mmmmmm+HH:MM' #T=' '

    _re_date= '(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)'
    _re_time= '(?P<hour>\d+):(?P<minute>\d+):(?P<second>\d+)'
    _re_microsecond = '(\.(?P<microsecond>\d+))?'                   #optional
    _re_timezone    = '((?P<tzhour>[+-]\d+):(?P<tzminute>\d+))?'    #optional
    _re_delimiter   = ' ' #T

    #_re = None     #set it to inheriting class to avoid recompile or None to force it

    _FORMAT = '%Y-%m-%d' +_re_delimiter + '%H:%M:%S'    #part of the ISO8601
    def textISO8601( me): return me.strftime( me._FORMAT)

    @classmethod
    def _re_compiled( klas):
        if klas._re is None: klas._re = re.compile(
                  klas._re_date
                + klas._re_delimiter     #T or whatever
                + klas._re_time
                + klas._re_microsecond   #optional
                + klas._re_timezone      #optional, ignored
                )
        return klas._re
    def __new__( klas, *args, **kargs):
        base = klas._base
        if args:
            a0 = args[0]
            if isinstance( a0, str):    #from str
                regexp = klas._re_compiled()
                base_args = klas._args
                m = regexp.match( a0 )
                match_dict = m and m.groupdict( default=0) or {}     #missing values =0
                kargs = dict( (k,int( match_dict.get(k,0))) for k in base_args)
                args = ()
            elif isinstance( a0, base): #copy ctor
                kargs = dict( (k,getattr( a0, k)) for k in klas._args)
                args = ()
        return base.__new__( klas._make_base and base or klas, *args, **kargs)

class datetime( _dt_base, _dt.datetime):
    _re = None  #request full
    _args = args_datetime
    _base = _dt.datetime
class date( _dt_base, _dt.date):
    _re = re.compile( _dt_base._re_date)    #preset
    _args = args_date
    _base = _dt.date
class time( _dt_base, _dt.time):
    _re = re.compile( _dt_base._re_time)    #preset
    _args = args_time
    _base = _dt.time


if __name__ == '__main__':
    #test
    d = datetime( '2004-02-26 15:34:39' )
    print d
    dnow = datetime.now()
    print str( dnow ), type(dnow), datetime.__name__
    assert dnow == datetime( str( dnow ) )
    print isinstance( d, datetime.__bases__)
    print issubclass( datetime, type(d))

    d = date( '2004-02-26' )
    print d, repr(d)

    print d.__class__
    d1 = _dt.date.today()
    print d1.__class__
    x = date( d1)
    print x, x.__class__

    class xdatetime( datetime):
        _re_delimiter = 'X'
        _re = None  #request full again
    d = xdatetime( '2004-02-26X15:34:39' )
    print d

# vim:ts=4:sw=4:expandtab
