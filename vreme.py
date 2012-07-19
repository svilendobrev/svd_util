#2006-2008 chefob sdobrev ico2
# -*- coding: utf8 -*-
'''
Universal Calendar Time and Pediods arithmetics;
physical, logical (next-working-day), inherit/compose, count, compare, overlap, cut
'''

from dateutil.relativedelta import *
from dateutil.rrule import *
import dateutil.parser as parser
import datetime as dt
from mix import neighbours

class BasicCalendar( object):
    ''' представя физическия календар, т.е. 'непрекъснато' време без неработни дни (периоди)
        някъв интерфейс
    '''
    pass

class BaseInitShow( object):
    _attrs = '' # set this below
    _str_sep = '|'

    def __init__( me, *args):   #args must be in _attrs order
        i = 0
        for each_attr in me._attrs.split():
            try:
                setattr( me, each_attr, args[ i])
            except IndexError:
                assert 0, 'wrong number of parameters to __init__ expected: '+ repr( me._attrs)
            i += 1

    def __str__( me):
        return me.__class__.__name__ + '.' + me._str_sep.join(  str( getattr( me, attr)) for attr in me._attrs.split())

    __repr__ = __str__

class TimeConversion( BaseInitShow):
    CanConvert, NoConvert = 'convertible', 'non-convertible'
    _attrs = 'code'
    _order = []
    @staticmethod       #zaemki ot merki posle shte gi obedinim/popravim XXX
    def setup_chain( table):
        for p,mul in table:
            mm=0
            for q,m in table:
                if m is None:
                    continue
                if mm:
                    q._convert[ p ] = mm
                    p._convert[ q ] = -mm
                if (p is q): # or ( p.typ != q.typ):
                    q._convert[ p ] = 1
                    #p._convert[ q ] = 1
                    mm=m
                else: mm*=m
                #print '@'.join( str(i) for i in [ p, q, mm, -mm])

    @classmethod
    def all( klas):
        assert klas._order
        return klas._order

    @classmethod
    def setup( klas, units):
        for k,v in units.iteritems():
            tc_inst = klas( code= k, *v )
            setattr( klas, k, tc_inst)
            klas._order.append( tc_inst)

    def __init__( me, ime, selector =None, code =None):
        ''' measure_to, measure_from - имената на мерките са в единствено число
            isDateRequired - дали иска контекстна дата
        '''
        BaseInitShow.__init__( me, *tuple( None for i in range( len(me._attrs))) )
        me.ime = (ime is None) and me.measure_from or ime   #choveshko ime
        me.typ = ( selector is None) and me.CanConvert or me.NoConvert
        me.selector = selector
        me.code = code
        if code == None:
            me.code = ime
        me._convert = {}

    def __repr__( me):   # needed by storeStrin
        return '.'.join( [ me.__class__.__name__, str( me.code)])

    def _razmnoji_mesechinata( me, from_date, times):
        broi_dni = 0
        each_dict = dict( [( me.selector, 1)] )
        #delta = relativedelta( **each_dict)
        delta = RelativeDelta( months= 1)
        each_date = from_date
        mesechinko = me.__class__.mesec
        for i in range( times):
            broi_dni += mesechinko.broi_dni( each_date)     #, calendar TODO
            each_date += delta
        return broi_dni

    def broi_dni( me, context_date):
        '''връща броя дни за периода започващ от контекстната дата за неконвертируемите периоди или 1'''
        if me.typ is me.NoConvert:
            coef_to_mesec = abs( me._convert[ me.mesec])
            if me == me.mesec:
                return rrule( MONTHLY,
                              dtstart= dt.datetime( context_date.year, context_date.month, 1),
                              bymonthday=(-1),
                              count=1,
                            ) [0].day #posledniat den ot mesec X
            res = me._razmnoji_mesechinata( from_date= context_date, times= coef_to_mesec) #mesechinko.broi_dni( context_date) # FIXME loop-вай тука
            return res
        return 1    #TODO

    '''     конвертируеми периоди                    неконвертируеми периоди (без контекстна дата)
            minuta  chas    den     sedmica sedmica2 mesec              trimesecie      polugodie godina

minuta      1       1/60    1/60*24                  1/broi_dni*60*24  1/broi_dni*60*24*3
chas        60      1       1/24    1/24*7  1/24*7*2 1/broi_dni*24     1/broi_dni*24*3
den         24*60   24      1       1/7     1/7*2    1/broi_dni        1/broi_dni*3
sedmica     7*24*60
sedmica2    2*7*24*60
mesec       broi_dni*24*60
trimesecie  3*broi_dni*24*60
polugodie   6*broi_dni*24*60
godina      12*broi_dni*24*60

брои_дни е сума за всеки месец от контекстната дата до края на периода
'''
    def convert( me, to, value, context_date =None):    #, calendar =BasicCalendar): TODO
        koef = me._convert[ to]
        if me.typ is me.NoConvert:
            broi_dni = me._razmnoji_mesechinata( context_date, value)
            koef *= broi_dni
        if koef < 0:
            return value/ koef
        return value * koef

TCS = TimeConversion
from dictOrder import dictOrder
if 10:
    TCS.setup(
        dictOrder( [
            ('sekunda',  ( 'секунда',)),
            ('minuta' ,  ( 'минута',)),     #timedelta(0,60)
            ('chas'   ,  ( 'час',)),
            ('den'    ,  ( 'ден',)),        #timedelta(1) = 24*chas
            ('sedmica',  ( 'седмица',)),
            ('sedmica2', ( '2седмици',)),
            ('mesec',    ( 'месец', 'months')),      # бр.дни= календар
    #       ( trimesecie  ( 'тримесечие', '')), # бр.дни= календар
    #       (polugodie   ( 'полугодие', NoConvert)),  # бр.дни= календар
            ('godina'    , ( 'година', 'years')),     # бр.дни= календар
    #       (stoletie    ( 'век', NoConvert)),        # бр.дни= календар
    #       (hiliadoletie( 'хилядолетие', NoConvert)),# бр.дни= календар
        ]
        )
    )

if 10:
    _time_conversions = [
        ( TCS.sekunda,      60,  ),
        ( TCS.minuta,       60,  ),
        ( TCS.chas,         24,  ),
        ( TCS.den,          7,   ),
        ( TCS.sedmica,      2,   ),
        ( TCS.sedmica2,     None,   ), # ами сега FIXME ко прайм тука
#    ]
#    _time_conversions2 = [
        ( TCS.mesec,        12,   ),
#        ( TCS.trimesecie,   2,   ),
#        ( TCS.polugodie,    2,   ),
        ( TCS.godina,       100,  ),
#        ( TCS.stoletie,     1000,),
#        ( TCS.hiliadoletie, 0,),
    ]
    TCS.setup_chain( _time_conversions)
#    TCS.setup_chain( _time_conversions2)
    TCS.mesec._convert[ TCS.den] = 1       # FIXME

DELTA_METHODS = 'years months days hours minutes seconds microseconds'
class RelativeDelta(object):
    def __init__( me, *args, **kargs):
        me._delta = relativedelta( *args, **kargs)

    @staticmethod
    def from_measure( measure, value=1):
        measures = {
            TCS.sekunda : 'seconds',
            TCS.minuta  : 'minutes',
            TCS.chas    : 'hours',
            TCS.den     : 'days',
            TCS.sedmica : 'weeks',
            #TCS.sedmica2: 'weeks', XXX value * 2 ?!
            TCS.mesec   : 'months',
            TCS.godina  : 'years',
        }
        kargs = {}
        kargs[ measures[ measure ] ] = value
        return RelativeDelta( **kargs)

    @staticmethod
    def reval(deltastr):
        kargs = dict( zip( DELTA_METHODS.split(),
                            map( int, deltastr.split(','))
                         )
                    )
        return RelativeDelta( **kargs)

    def __str__( me):
        return str( me._delta)

    def __repr__( me):
        return ('%(years)02d,%(months)02d,%(days)02d,%(hours)02d,%(minutes)02d,%(seconds)02d,%(microseconds)02d' %
                 vars(me.normalize()._delta) )

    def __getattr__( me, name):
        #print 'looking for %s' % name
        return getattr( me._delta, name)

    def __setattr__( me, name, value):
        if name not in DELTA_METHODS:
            object.__setattr__( me, name, value)
            return
        try:
            val = int( value)
        except ValueError, e:
            print e, 'wrong type of attribute %s - trying to set %s.' % ( name, value)
        else:
            setattr( me._delta, name, val)

    @staticmethod
    def from_relativedelta( rdelta):
        return RelativeDelta( **dict( [(k, v) for (k, v) in vars(rdelta).iteritems() if not k.startswith('_') ] ))

    def __add__( me, o):
        if isinstance( o, RelativeDelta):
            return me.from_relativedelta( o._delta + me._delta)
        elif isinstance( o, dt.datetime):
            return UniversalTime( o + me._delta)
        elif isinstance( o, int):
            return me.from_relativedelta( me._delta + relativedelta( days=o))
        else:
            print o.__class__
            raise Exception
            return o + me

    __radd__ = __add__

    def __sub__(me, o):
        if isinstance( o, RelativeDelta):
            return RelativeDelta.from_relativedelta( me._delta - o._delta)
        elif isinstance( o, relativedelta):
            return me._delta - o
        raise AssertionError('tralala %s' % type(o))

    def __rsub__(me, o):
        if isinstance( o, dt.datetime):
            return UniversalTime(o - me._delta)
        raise AssertionError('tralala %s' % type(o))

    def __cmp__( me, o):
        return cmp(me._delta, o)

    def __eq__( me, o):
        return not bool( me.__cmp__(o))

    def __nq__( me, o):
        return not me.__eq__(o)

    def normalize(me):
        ot = UniversalTime.now()
        do = ot + me
        return do - ot

class UniversalTime( object):
    def __init__( me, time ='', precision =None, context =None):
        if isinstance( time, UniversalTime):
            #XXX need to explicitly specify precision/context; else uses source ones
            me.initial = time.initial
            me.exact_time = time.exact_time
            if precision is not None: me._round( precision)
            context = context or time.context
        else:
            if isinstance( time, basestring):
                me.initial = time
                me.exact_time = me.fromString( time, context=context)
            elif isinstance( time, dt.datetime):
                me.initial = time.strftime('%Y%m%d%H%M%S')
                me.exact_time = time
            elif isinstance( time, dt.date):
                me.initial = time.strftime('%Y%m%d')
                me.exact_time = me.fromString( me.initial, context=context)
            else:
                raise AssertionError( str(time.__class__) + ' not supported')

            if precision is None: precision = TCS.sekunda
            me._round( precision )

        me.context = context

    @staticmethod
    def beginOfUniverse():
        return UniversalTime( dt.datetime( 1900, 1, 1))
    begin = beginOfUniverse

    @staticmethod
    def endOfUniverse():
        return UniversalTime( dt.datetime( 3000, 1, 1))
    end = endOfUniverse

    @staticmethod
    def now():
        return UniversalTime( dt.datetime.now())

    @staticmethod
    def fromString( timestr =None, context =None):
        return parser.parse( timestr, default= context)

    @staticmethod
    def toString( time, timefmt =None):
        ''' Приема дата обект, връща стринг. Указва се формат( като стринг). '''
        if not timefmt:
            timefmt = '%Y-%m-%d'
        timestr = time.strftime( timefmt)
        return timestr

    def to_string(me, timefmt):
        return me.toString( me.exact_time, timefmt)

    def convertTo( me, conversion_typ= dt.datetime, context =None):    #XXX
        pass

    @staticmethod
    def Round( dtime, precision):
        prec_map = {
            TCS.sekunda: '%Y%m%d%H%M%S',
            TCS.minuta : '%Y%m%d%H%M',
            TCS.chas   : '%Y%m%d%H00', #00 is needed for the parser
            TCS.den    : '%Y%m%d',
        }
        fmt = prec_map[precision]
        return dt.datetime.strptime( dtime.strftime(fmt), fmt)

    def round( me, precision):
        return UniversalTime( me.Round( me.exact_time, precision))

    def _round( me, precision):
        #in place

        #prec_map = {
        #    TCS.sekunda: '%Y%m%d%H%M%S',
        #    TCS.minuta : '%Y%m%d%H%M',
        #    TCS.chas   : '%Y%m%d%H00', #00 is needed for the parser
        #    TCS.den    : '%Y%m%d',
        #}
        #fmt = prec_map[precision]
        #me.exact_time.strptime( dtime.strftime(fmt), fmt)

        me.exact_time = me.Round( me.exact_time, precision)

    def compare( me, other, precision=TCS.sekunda):
        selftime = me.exact_time
        if isinstance( other, dt.datetime):
            othertime = other
        elif isinstance( other, dt.date):
            othertime = dt.datetime( other.year, other.month, other.day)
        elif isinstance( other, basestring):
            othertime = UniversalTime(other).exact_time
        elif isinstance( other, UniversalTime):
            othertime = other.exact_time
        else:
            raise NotImplementedError( 'can\'t compare UniversalTime to %s' % other.__class__)
        return cmp ( selftime, othertime)

    __cmp__ = compare

    def __repr__(me):
        return me.__class__.__name__ + '( ' + repr( me.exact_time) + ')' # eval()
        return me.initial + ' -> ' + repr( me.exact_time )

    def __str__(me):
        return 'UT: ' + str(me.exact_time)

    def __add__( me, o):
        if isinstance( o, int):
            o = RelativeDelta( days=o) #chefo's request
        if isinstance( o, (dt.timedelta, RelativeDelta)):
            return UniversalTime( me.exact_time + o)

        raise TypeError( 'unsupported type[%s] for operation' % o.__class__)

    __radd__ = __add__

    def __sub__(me, other):
        if isinstance( other, int):
            other = RelativeDelta( days=other) #chefo's request
        if isinstance( other, (dt.timedelta, RelativeDelta)):
            return UniversalTime( me.exact_time - other)

        return RelativeDelta( dt1=me.exact_time, dt2=UniversalTime(other).exact_time)

    def __lt__( me, other): return me.compare( other) < 0
    def __le__( me, other): return me.compare( other) <= 0
    def __gt__( me, other): return me.compare( other) > 0
    def __ge__( me, other): return me.compare( other) >= 0
    def __eq__( me, other): return me.compare( other) == 0
    def __ne__( me, other): return me.compare( other) != 0

    #these fall into __getattr
    #def timetuple( me): #datetime needs this when comparing from the right side
    #    return me.exact_time.timetuple()
    #def __hash__( me):
    #    return hash( me.exact_time)

    def __getattr__( me, name):
        #print 'looking for %s' % name
        return getattr( me.exact_time, name)

    def UIstr( me):
        return me.to_string('%Y-%m-%d')

#17 седмици колко месеца са??? some conversion maybe - TODO
class Period( object):
    '''представя затворен отляво, отворен отдясно интервал от време'''

    class PeriodException( Exception): pass

    def __init__( me, ot =None, do =None, size =None, precision =TCS.den):
        ''' ot, do, size - this can be created by any two of them.
        any of this can be calendared or simple thus requiring context workcalendar or not.'''
        me.precision = precision # to day, hour...must be considered by cmp, maybe by hash too???
        #me.initial_ot = ot #ne znam dali ni triabwat
        #me.initial_do = do

        if size and (ot is do is None or ot and do):
            raise me.PeriodException( 'valid ctors are (ot), (ot,do), (ot,size), (do), (do,size)')

        if do is not None: do = UniversalTime( do)
        if ot is not None:
            ot = UniversalTime( ot)
            if size is not None: do = ot + size
        elif do is not None:
            if size is not None: ot = do - size
        if ot is None: ot = UniversalTime.beginOfUniverse()
        if do is None: do = UniversalTime.endOfUniverse()
        assert ot <= do
        me.ot = ot
        me.do = do

    def size( me):
        #return RelativeDelta( dt1=me.do.exact_time, dt2=me.ot.exact_time)
        return (me.do.exact_time - me.ot.exact_time).days

    def __cmp__(me, o):
        r = cmp(me.ot, o.ot)
        return r or cmp(me.do, o.do)

    def __eq__( me, o):
        if not isinstance( o, me.__class__):
            return False
        return not bool( me.__cmp__(o))

    def multiply( me, n):
        '''returns 'n' consequent Periods of same size'''
        res = [me]
        for i in range( n-1):
            res.append( Period( ot=res[-1].do, size=me.size()) )
        return res

    def split( me, n):
        '''returns the Period splitted in 'n' Periods'''
        res = []
        size = me.size() / n
        for i in range( n):
            if not i:
                res.append( Period( ot=me.ot, size=size))
            else:
                res.append( Period( ot=res[-1].do, size=size))
        return res

    def extend( me, n):     #or expand?
        'returns n-times longer Period'
        return Period( ot= me.ot, size= n*me.size() )

    def shrink( me,n):      #or reduce,contract?
        'returns n-times shorter Period'
        return Period( ot=me.ot, size=me.size()/n )

    def __add__( me, other):
        retmap = { int : me.shift,
                   dt.timedelta: me.add_delta,
                   RelativeDelta: me.add_delta,
                   Period: me.add_interval
                 }
        otype = type(other)
        f = retmap.get( otype, None)
        if f: return f( other)
        raise me.PeriodException( '.add cannot take %s, needs one of %s' % (otype, retmap.keys() ) )

    __mul__ = multiply
    __div__ = split
    __rmul__ = __mul__
    __radd__ = __add__

    def add_days( me, other):
        return me.add_delta( dt.timedelta( days=other) )

    def add_month( me, nr=1):
        return me.add_delta( RelativeDelta( months=nr) )

    def add_year( me, nr=1):
        return me.add_delta( RelativeDelta( years=nr) )

    def add_delta( me, delta):
        return Period( me.ot, me.do + delta)

    def add_interval( me, other):
        if me.overlap( other):
            return PeriodCollection( [ Period( min( me.ot, other.ot), max( me.do, other.do)) ] )
        else:
            return PeriodCollection( [ me, other ] )


    def __and__(me, other):
        if me.overlap( other):
            res = Period( max( me.ot, other.ot), min( me.do, other.do))
        else:
            res = None
        return res

    def shift( me, shift):
        if isinstance( shift, int):
            s = RelativeDelta( days=shift)
        elif isinstance( shift, (dt.timedelta, RelativeDelta)):
            s = shift
        else:
            assert 0, 'what is this: %s' % type(shift)
        return Period( me.ot + s, me.do + s)

    def __sub__( me, sub):
        if isinstance( sub, int):
            return me.shift( shift = -sub)
        if isinstance( sub, (dt.timedelta, RelativeDelta)):
            return Period( me.ot, me.do - sub)
        if isinstance( sub, Period): #XXX ??? towa trebe li?
            if me & sub:
                if sub.ot > me.ot and me.do > sub.do:
                    # t1            t2   ## t1-t3 i t4-t2
                    #     t3    t4       ##
                    return [
                        Period( me.ot,  sub.ot),
                        #Period( sub.ot, sub.do),
                        Period( sub.do,  me.do),
                    ]
                elif sub.ot > me.ot and me.do <= sub.do:
                    # t1      t2         ## t1-t3
                    #     t3     t4      ##
                    return [
                        Period( me.ot, sub.ot),
                    ]
                elif sub.ot <= me.ot and me.do > sub.do:
                    #     t1     t2
                    # t3      t4
                    return [
                        Period( sub.do, me.do),
                    ]
                elif sub.ot <= me.ot and me.do <= sub.do:
                    #    t1  t2          ## t1-t2 ili nishto?!
                    # t3        t4       ##
                    return [ ]
            else:
                return [ me ] # ne se zastypwat, nishto ili nie?
        raise me.PeriodException('need int, timedelta or Period received %s' % type( sub))

    __rsub__ = __sub__


    def overlap( me, other):
        ot = max( me.ot, other.ot)
        do = min( me.do, other.do)
        return ot < do

        return ( me.containsDate( other.ot) or
                 me.containsDate( other.do) or
                 other.containsDate( me.ot) or
                 other.containsDate( me.do)
               )

    def containsDate( me, date, include_to =False):
        z = (date <= me.do) if include_to else (date < me.do)
        return ( date >= me.ot and z ) #FIXME включително края или не?

    def containsInterval( me, interval):
        return me.containsDate( interval.ot) and me.containsDate( interval.do, True)

    def contains( me, other, include_to =False):
        if isinstance( other, (dt.datetime, UniversalTime)):
            return me.containsDate( other, include_to =include_to)
        elif isinstance( other, Period ):
            return me.containsInterval( other)
        raise me.PeriodException('need time or Period, received %s' % type( other))

    def adjacentTo( me, other):
        return me.do == other.ot # or me.ot == other.do #

    def as_delta(me):
        return me.do - me.ot

    def __str__( me):
        return '[ '+ ' : '.join( i.to_string("%Y%m%d") for i in [me.ot, me.do]) +' )'
    def __repr__( me):
        return me.__class__.__name__ + '(' + str(me) + ')'

    def _get_ot(me):
        return me._ot
    def _get_do(me):
        return me._do
    def _set_ot(me, ot):
        me._ot = UniversalTime(ot, precision=me.precision)
    def _set_do(me, do):
        me._do = UniversalTime(do, precision=me.precision)
    ot = property( _get_ot, _set_ot)
    do = property( _get_do, _set_do)

    def split( me, precision=TCS.den, **kargs):
        '''  kargs should contain one of these keys:
             freq,              YEARLY, MONTHLY, WEEKLY, DAILY, HOURLY, MINUTELY, SECONDLY
             dtstart =None,     date_start
             interval =1,       freq+=interval iteration
             wkst =None,        MO, TU, WE, TH, FR, SA, SU - week start day
             count =None,       how many results to be generated, not needed if until is set
             until =None,       date_end
             bysetpos =None,
             bymonth =None,     (1,12), (1, 2..)
             bymonthday =None,      == || == za dni na mesec, podyrzha negativni indeksi
             byyearday =None,
             byeaster =None,
             byweekno =None,
             byweekday =None,   MO, TU, WE, TH, FR, SA, SU
             byhour =None,      00-24
             byminute =None,    00-60
             bysecond =None,    00-60
             cache =False XXX
        '''
        freq    = kargs.pop( 'freq', MONTHLY)
        dtstart = kargs.pop( 'dtstart', me.ot)
        until   = kargs.pop( 'until', me.do)

        rule = rrule( freq= freq, dtstart= dtstart.exact_time, until= until.exact_time, **kargs)
        days = sorted( set( rule) | set([ me.ot.exact_time, me.do.exact_time]))
        periods = [ Period( prev,next, precision=precision)
                        for prev,next in neighbours( days)
                    ]
        return PeriodCollection( periods)

    def __getitem__( me, i):
        raise NotImplementedError, 'Use ot, do'
        if i not in (0,1,-1): raise IndexError,i   #за да работи a,b=period
        if i: return me.do
        return me.ot

    @staticmethod
    def from_date( date, measure, move_to_logical_start=True, from_given_date=False):
        r = {
            TCS.sedmica : Period.week_from_date,
            TCS.mesec   : Period.month_from_date,
            TCS.godina  : Period.year_from_date,
        }
        period = r[measure](date, move_to_logical_start or from_given_date)
        if from_given_date:
            period.ot = date
        return period

    @staticmethod
    def week_from_date(date, move_to_logical_start=True):
        t = UniversalTime(date)
        delta = RelativeDelta(weeks=1)
        if move_to_logical_start:
            start_date = rrule(WEEKLY, dtstart=t.exact_time, byweekday=MO)[0]
            if start_date > t: #next monday
                start_date -= delta
        else:
            start_date = t
        return Period( start_date, delta=delta)

    @staticmethod
    def month_from_date(date, move_to_logical_start=True):
        t = UniversalTime( date)
        start_date = dt.datetime( t.year, t.month, move_to_logical_start and 1 or t.day)
        return Period( start_date, start_date + RelativeDelta( months=1))

    @staticmethod
    def year_from_date(date, move_to_logical_start=True):
        t = UniversalTime( date)
        month = (t.month, 1)[ move_to_logical_start]
        day   = (t.day,   1)[ move_to_logical_start]
        start_date = dt.datetime( t.year, month, day)
        return Period( start_date, start_date + RelativeDelta( years=1))

class VremeContext( object):
    '''stub only till now'''    #TODO de-stub-bing
    def __init__( me, kalendar =None):
        me.kalendarche = kalendar

    def year( me):
        return dt.datetime.now().year

    def month( me):
        return 5 #dt.datetime.now().month

    def as_universal_time( me ):
        return UniversalTime( ma.as_datetime())

    def as_datetime( me):
        return

def get_context( context):
    'тука ще има ракети и времомашини'  #TODO
    return context

class PeriodCollection( object):
    ''' това отделен клас ли е или Period да свърши и това?''' # XXX
    ''' тук явно влизат и колекция от UniversalTime (единични времеви обекти),
    представени като интервал [ot, ot]
    '''
    def __init__( me, timeIntervalList):
        me.collection = list( timeIntervalList)

    def __add__( me, timeIntervalList):
        if isinstance( timeIntervalList, PeriodCollection):
            timeIntervalList = timeIntervalList.collection
        assert isinstance( timeIntervalList, list)
        col = me.collection + timeIntervalList
        return PeriodCollection( col)

    # има същия интерфейс като Period + обединение
    def __str__( me):
        s = ''
        for i in me.collection:
            s += str(i) + '\n'
        return s

    def size( me, context =None):
        r = 0
        for p in me.collection:
            r += p.size()
        return r

    def as_delta(me):
        r = RelativeDelta()
        for p in me.collection:
            r += p.as_delta()
        return r

    def sort(me):
        me.collection.sort()

    def simplify( me, collection=None):
        ''' обединяване на съседни или застъпващи се интервали ако може'''
        if collection is None:
            col = me.collection
        else:
            col = collection
        col.sort()
        ncol = []
        for next in col:           #prowerka za sysedni interwali
            if ncol:
                prev = ncol[-1]
                if prev.adjacentTo( next):
                    ncol[-1] = (prev + next)[0]
                    continue
            ncol.append( next)
        ncol.sort()
        ncol2 = []
        for next in ncol:          #prowerka za wlojeni interwali
            if ncol2:
                prev = ncol2[-1]
                res = prev + next
                if res.size() == 1 and res[0] == prev:
                    continue
            ncol2.append( next)

        if len(col) == len(ncol2):          #ne sa nastypili promeni
            return PeriodCollection( ncol2)
        else:
            return me.simplify( ncol2)  #puskame pak cialata shema

    def __getitem__( me, idx):
        return me.collection[ idx ]

    def __iter__( me):
        return iter(me.collection)

    def intersect( me, other, context =None):
        pass    #????

    def razcepvane( me, kude):
        pass

    def sa_susedni( me, other):
        pass

    def union( me, other, context =None):
        pass
    # TODO зацепване, разцепване, прицепване на обединение на интервали (съседни, застъпващи се, без сечение) по различни стратегии за обединени (5-6 вида)
    # TODO всички аритметики с число, момент във времето, интервал от време

    #specific query methods - needed often
    #TODO първия работен ден >= 5то число на месеца - как се задава???
    def _karamboliraiSKalendar( me, nth_day_of_month, context, isBefore =True):
        'съвсем примерна имплементация'
        context = get_context( context) #stub
        if isBefore:
            first_day = 1
            last_day = nth_day_of_month
        else:
            first_day = nth_day_of_month
            last_day = 32
        last_day_of_month = rrule( MONTHLY,
                                   dtstart= dt.datetime( context.year(), context.month(), 1),
                                   bymonthday= (-1),
                                   count= 1,
                                 ) [0].day
        last_day_by_month = min( last_day_of_month, last_day)
        ruleset = rruleset()
        r = rrule( MONTHLY,
                   bymonthday= range( first_day, last_day),
                   dtstart= dt.datetime( context.year(), context.month(), first_day),
                   until= dt.datetime( context.year(), context.month(), last_day_by_month),
                 )
        ruleset.rrule( r)
        for neraboten in context.kalendarche.holidays():
            ruleset.exdate( neraboten)
        return ruleset

    # трябва да има и първия и последния работен ден след/преди дата XXX
    def firstWorkingDayAfter( me, nth_day_of_month, context =None):
        l = list( me._karamboliraiSKalendar( nth_day_of_month, context, isBefore = False))
        return min( l)

    def lastWorkingDayBefore( me, nth_day_of_month, context =None): #last_day is 32 ;)
        l = list( me._karamboliraiSKalendar( nth_day_of_month, context, isBefore = True))
        return max( l)
    # когато ти трябва интервал от шест месеца назад (интервали назад) по кой
    # работен календар се смята (към момента на поискване или някакъв друг - двубременност)

if 0:
    class WorkGraphic(object):
        def __init__( me, kalendar):
            me.raboten_kalendar = kalendar
            me.working_intervals = []

class RecurrentPeriod( Period):
    #oshte kolko chesto se povtaria
    def __init__( me, ot, do, chestota= None, precision= None):
        Period.__init__( me, ot, do, precision)
        me.chestota = chestota

class WorkCalendar( BasicCalendar):
    ''' подлежи на извличане чрез механизЪма на наследяване/засенчване, реализиран другаде...
    '''
    #TODO xxx_intervali да връща PeriodCollection
    @staticmethod
    def weekend_days( period):
        ot = period.ot.exact_time
        do = period.do.exact_time
        return list(rrule( WEEKLY, dtstart=ot, until=do, byweekday=(SA, SU)))

    def __init__( me, holidays):
        me._holidays = []
        me.append_holidays( holidays)

    def __repr__( me):
        return repr( me._holidays[:10])  #XXX

    def append_holidays( me, h):
        me._holidays += h
        me._holidays = sorted( set( me._holidays))

    def holidays( me):
        return me._holidays

    def working_intervals( me, period):
        #връща колекция от отворени отляво интервали, които са работни периоди(дни)
        assert isinstance( period, Period)
        ot = period.ot
        do = period.do
        res = [ Period(ot, do)]
        for holi in me._holidays:
            if ot <= holi and holi <= do:
                res[-1].do = holi
                new_ot = holi + RelativeDelta( days=1)
                if new_ot >= do: break
                res.append( Period( new_ot, do))

        end = res[-1] #rowichkame da namerim posledniqt raboten den predi kraq na interwala
        oneday = RelativeDelta( days=1)
        while (end.do - oneday in me._holidays):
            end.do -= oneday

        for i in res[:]:
            if i.ot in me._holidays:
                res.remove( i)
        return PeriodCollection(res)

    def non_working_intervals( me, period):
        ot = period.ot
        do = period.do
        res = []
        oneday = RelativeDelta( days=1)
        for d in me._holidays:
            if d < ot: continue
            if d >= do: break
            if res and res[-1].do == d:
                res[-1].do += oneday
                continue
            res.append( Period(d, d+oneday))

        if res and res[-1].do > do:
            res[-1].do = do
        return PeriodCollection(res)

    def _len_interval( me, period, interval_fx):
        collection = interval_fx( period)
        res = 0
        for p in collection:
            res += p.size() #тука XXX май трябва да е наобратно-Period da vika WorkCalendar len...
        return res

    def len_working_interval( me, period):
        return me._len_interval( period, me.working_intervals)

    def len_nonworking_interval( me, period):
        return me._len_interval( period, me.non_working_intervals)

    def len_working_days(me, date, measure):
        period = Period.from_date( date, measure)
        return me.len_working_interval( period)

    def is_non_working_day( me, univ_time):
        return univ_time.round(TCS.den) in me._holidays

    def is_working_day( me, univ_time):
        return not me.is_non_working_day( univ_time)

    def __str__( me):
        return me.__class__.__name__+ '[ \n' + ', \n'.join( str(i) for i in me._holidays) + ']'

    def to_string(me, format='%Y-%m-%d'):
        return ', '.join( UniversalTime(i).to_string( format) for i in me.holidays())

def get_test_calendar():
    holidays_in_bg_2008 = list(rrule( WEEKLY, dtstart=dt.datetime(2008,1,1), until=dt.datetime(2008,12,31), byweekday=(SA, SU)))
    wc2008 = WorkCalendar( holidays_in_bg_2008)
    wc2008.append_holidays( [dt.datetime( 2008, 12, i) for i in range(23, 32)] )
    return wc2008


if __name__ == '__main__':
    def dede():
        print 20*']' + 'Свети ПАРис - не подлежи на автоматизация:'
        #rule = rrule( MONTHLY, byweekday=FR(+1), count= 10) #experience deposed this
        rule = rrule( MONTHLY, byweekday= FR,
            bymonthday= (3,4,5,6,7,8,9),    #1st and 2nd days of a month are doomed ;)
            count= 10, dtstart= dt.datetime( 2008, 1, 1))
        for sveti_parastas in rule: print sveti_parastas
        print 20*']'
        return rule
    rule = dede()

    ot = dt.datetime( 2008, 5, 1)
    do = dt.datetime( 2008, 5, 31)
    pochivni = [ dt.datetime( 2008, 5, 24), dt.datetime( 2008, 5, 2) ]
    wc = WorkCalendar( pochivni)
    wc.append_holidays( list( rrule( WEEKLY, byweekday=[SA, SU], until=dt.datetime(2008,6,1), dtstart= dt.datetime( 2008, 4, 1))) ) #weekends
    print wc
    print 'working_intervals:\n[\n' + '\n'.join( str(i) for i in wc.working_intervals( Period(ot, do))) +'\n]'
    ot = dt.datetime( 2008, 5, 7)
    print 'working_intervals:\n[\n' + '\n'.join( str(i) for i in wc.working_intervals( Period(ot, do))) +'\n]'

    ot = dt.datetime( 2008, 4, 1)
    do = dt.datetime( 2008, 5, 26)
    print 'non_working_intervals:\n'+'\n'.join(str(i) for i in wc.non_working_intervals( Period(ot, do)))
    print '\nLR:', wc.len_working_interval( Period(ot, do))
    print '\nLN:', wc.len_nonworking_interval( Period(ot, do))
    print

    rti = RecurrentPeriod( ot, do, chestota= list(rule))
    #print rti, rti.chestota

    t1 = UniversalTime().fromString( '20080101')
    print t1, t1.__class__

    t2 = UniversalTime().fromString( '200801011222')
    print t2, t2.__class__

    t2 = UniversalTime().fromString( '2008-01-01 12:22')
    print t2, t2.__class__

    t2 = UniversalTime().fromString( '20080101T12:22:55')
    print t2, t2.__class__

    t2 = UniversalTime().fromString( 'jan 03T12:22:55', context= dt.datetime( 2005, 1, 1))
    print 'xxxxxxxxx', t2, t2.__class__

    print
    kintext = VremeContext( wc)
    t = PeriodCollection( []).firstWorkingDayAfter( 4, kintext)
    print 'firstWorkingDayAfter 4th:', t

    t = PeriodCollection( []).lastWorkingDayBefore( 4, kintext)
    print 'lastWorkingDayBefore 4th:', t
    #тез горните два метода май съм към календара, а не тука ???

    print 20*'-'
    def check_broi_dni( mera, context_date, verno):
        miarka= getattr( TCS, mera)
        res = eval( 'miarka.broi_dni( context_date)')
        print '%s %s: %i' % ( mera, str( context_date), res)
        assert res == verno, ':'.join( str( i) for i in ( mera, context_date, res))

    check_broi_dni( 'godina', dt.datetime( 2008, 2, 5), 366)
    check_broi_dni( 'godina', dt.datetime( 2008, 3, 5), 365)
    check_broi_dni( 'mesec', dt.datetime( 2008, 2, 5), 29)
    check_broi_dni( 'mesec', dt.datetime( 2007, 2, 5), 28)
    #check_broi_dni( 'chas', dt.datetime( 2008, 3, 5), 365)
    #check_broi_dni( '', dt.datetime( 2008, 3, 5), 365)

    print 20*'-'
    def check_convert( mera_from, mera_to, value, verno, context_date =None):
        miarka_ot= getattr( TCS, mera_from)
        miarka_kam= getattr( TCS, mera_to)
        res = eval( 'miarka_ot.convert( miarka_kam, value, context_date)')
        print '%s->%s %s: %i' % ( mera_from, mera_to, str( context_date), res)
        assert res == verno, ':'.join( str( i) for i in ( mera_from, mera_to, context_date, res))
    #конвертируеми
    if 0:
        check_convert( 'sedmica', 'den', 3, 21)
        check_convert( 'den', 'sedmica',  3, 5)
    #неконвертируеми
    check_convert( 'mesec', 'den',  1, 28, dt.datetime( 2007, 2, 5))
    check_convert( 'mesec', 'den',  1, 31, dt.datetime( 2008, 3, 5))
    check_convert( 'mesec', 'den',  1, 29, dt.datetime( 2008, 2,25))
    check_convert( 'mesec', 'den',  1, 31, dt.datetime( 2008, 3, 5))
    #неконвертируеми-конвейртируеми
    #check_convert( 'sedmica', 'godina', 3, 21, dt.datetime( 2008, 3, 5))
    #check_convert( 'den', 'mesec',  1, dt.datetime( 2008, 3, 5), 31)

    if 0:
        for p,mul in _time_conversions:
            for q,mul in _time_conversions:
                print 'coef for:', 1, p, ' = ',
                try: print p._convert[ q],
                except KeyError: print '!cant',
                print q

#    #raise SystemExit
#    for p,mul in _time_conversions:
#        for q,mul in _time_conversions:
#            print 1, p, ' = ', p.convert( q, 1.0, context_date= dt.datetime( 2008, 3, 5)), q
#
#    raise SystemExit
#    for p,mul in _time_conversions:
#        for q,mul in _time_conversions:
#            print 1, p, ' = ', p.convert( q, 1.0, context_date= dt.datetime( 2008, 2, 5)), q
#
#    print TCS.den.convert( TCS.mesec, 10, dt.datetime( 2008, 2, 25))

    print '1'*20, 'ToString Proba'
    time1 = dt.datetime( year= 2008, month= 4, day= 5)
    tmp = UniversalTime().toString( time1)
    print time1, '==>>', tmp

    fmt = '%Y-%m'
    tmp1= UniversalTime().toString( time1, timefmt = fmt)
    print time1, '==>>', tmp1

# vim:ts=4:sw=4:expandtab
