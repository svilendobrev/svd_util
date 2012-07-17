# ~2004
'parse+create of cron/crontab files'

import datetime
import time
import re
import threading

_token_ids = [ 'minute', 'hour', 'dom', 'month', 'dow', ]
_split_entry = re.compile( '[ \t]+'.join( [ '(?P<%s>[-*0-9,/]+)' % key for key in _token_ids ] ) +
                           '[ \t]+(?P<task>[- \.\w]+)'
                          )

_valid_ranges = {}
_valid_ranges['minute']  = (0, 59)
_valid_ranges['hour'] = (0, 23)
_valid_ranges['dom'] = (1, 31)
_valid_ranges['month'] = (1, 12)
_valid_ranges['dow'] = (0, 7)

class ParseError( Exception ):
    pass

class crontab:
    """ A class which parses crontab(5) style entries. """

    LIST_DELIMITER = ','
    RANGE_DELIMITER = '-'
    STEP_DELIMITER = '/'
    WILDCARD = '*'

    class entry:
        def __init__( me ):
            """ A dummy constructor. """
            pass

        def __str__(me):
            """ Returns a string representation of the given instances. """

            return ','.join( [ '%s:%s' % (k,getattr( me,k)) for k in _token_ids ] )

        def matches( me ):
            """ """
            datetime_now = datetime.datetime.now()

            if (datetime_now.month in me.month and
               (datetime_now.day in me.dom or datetime_now.weekday() in me.dow) and
               datetime_now.hour in me.hour and
               datetime_now.minute in me.minute):
                return True
            return False

    def __init__( me, entries ):
        """ Initialize key data members.

                `entries' a list of crontab(5) like entries. """

        me.entries = []
        me.parse( entries )

    def islist( me, val ):
        return crontab.LIST_DELIMITER in val

    def isrange( me, val ):
        return crontab.RANGE_DELIMITER in val

    def isstep( me, val ):
        return crontab.STEP_DELIMITER in val

    def iswildcard( me, val):
        return crontab.WILDCARD in val

    def parse_wildcard( me, field, val ):
        rstep = 1

        if val[0] != crontab.WILDCARD:
            raise ParseError, ('parse_wildcard: the asterisk must be the '
                                'first char in a wildcard field: %s' % val)
        if len( val ) > 1:
            if me.isstep( val[1:] ):
                dummy, rstep = me.parse_pair( val, crontab.STEP_DELIMITER )
                rstep = int( rstep )
                if rstep not in range(_valid_ranges[field][0], _valid_ranges[field][1]):
                    raise Parse, ("parse_wildcard: invalid step value `%d' " % rstep +
                                  "for field `%s': %s" % (field, val))
            else:
                raise ParseError, ('parse_wildcard: the asterisk can be followed '
                                    'only by a step: %s' % val)

        return range( _valid_ranges[field][0], _valid_ranges[field][1] + 1, rstep )

    def parse_pair( me, val, sep ):
        ret = val.split( sep, 2 )
        if len( ret ) > 2:
            raise ParseError, 'parse_pair: too many tokens: %s' % val
        return ret

    def parse_list( me, val ):
        l = val.split( crontab.LIST_DELIMITER )
        result = []

        for i in l:
            if me.isrange( i ):
                r = filter( lambda x: x not in result, me.parse_range( i ) )
                result.extend( r )
            else:
                if not i in result:
                    result.append( int( i ) )

        result.sort()
        return result

    def parse_range( me, val ):
        a_range = ''
        step = None

        if me.isstep( val ):
            a_range, step = me.parse_pair( val, crontab.STEP_DELIMITER )
        else:
            a_range = val
            step = 1

        rstart, rend = me.parse_pair( a_range, crontab.RANGE_DELIMITER )

        if rstart > rend:
            raise ParseError, 'parse_range: start > end: %s' % val

        return range( int( rstart ), int( rend ) + 1, int( step ) )

    def parse( me, entries ):
        for entry in entries:
            match = _split_entry.match( entry )
            if match is None:
                raise ParseError, "parse: could not split the entry `%s'" %(entry)

            d = match.groupdict()
            e = crontab.entry()
            for k, v in d.iteritems():
                l = []

                if k == 'task':
                    l = v.split( ' ' )
                    setattr( e, k, l )
                    continue

                if me.iswildcard( v ): l = me.parse_wildcard( k, v )
                elif me.islist( v ): l = me.parse_list( v )
                elif me.isrange( v ): l = me.parse_range( v )
                else: l.append( int( v ) )

                if min(l) < _valid_ranges[k][0] or max(l) > _valid_ranges[k][1]:
                    raise ParseError, "parse: invalid value `%s' for the `%s' field. valid values are in the range %s-%s" % (v, k, _valid_ranges[k][0], _valid_ranges[k][1])

                setattr( e, k, l )

            me.entries.append(e)

class cron( threading.Thread ):

    def __init__( me, crontab, allowed_jobs = {}, **kargs ):
        threading.Thread.__init__( me, group = None, target = None, name = me.__class__.__name__ )
        me.crontab = crontab
        me.__allowed_jobs = allowed_jobs
        me.__cancel = False

        me.setDaemon( True )

    def cancel( me ):
        me.__cancel = True

    def run( me ):
        while True:
            # Honour cancel requests
            if me.__cancel: break

            # Wake up each minute and check if there is a task
            # to run .
            time.sleep( 60 - datetime.datetime.now().second )

            # Parse the crontab
            _crontab = crontab ( me.crontab )

            for i in _crontab.entries:
                if i.matches():
                    try:
                        target = me.__allowed_jobs[ i.task[0] ]
                    except KeyError:
                        # TODO: print...
                        print "Job %r not allowed!" % i.task[0]
                        continue

                    args = i.task[1:]
                    thr = threading.Thread( target = target, name = 'cronjob',
                                        args = args )
                    thr.start()

if __name__ == '__main__':

    c = [
            '*/3 * * * *',
            '*/1 6 * * *',
#            '* * 400 * *',
#            '0-59/3 0-23/1 1-31/1 1-12/1 0-7/1',
        ]

    cronthread = cron( c )
    cronthread.start()
    cronthread.join()

    if 0:
        tmp = crontab( c )

        while 1:
            time.sleep( 60 - datetime.datetime.now().second )
            print 'Woke up'
            for e in tmp.entries:
                if e.matches():
                    print "We've got a match!", str (datetime.datetime.now())

# vim:ts=4:sw=4:expandtab
