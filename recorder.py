# hstanev sdobrev 2007-9
'recorder/player of object usage'

class MethodCallData( object):
    def __init__( me, name, *a, **k):
        me.name = name
        me.args = list(a) # args is tuple
        me.kargs = k

    def __str__( me):
        return '%s args=%s kargs=%s' % (me.name, me.args, me.kargs)

class Recorder( object):
    ''' Records all requests so they can be played back later to another object.'''

    def __init__( me, rec_context =None):
        me.rec_context = rec_context # None if method results don't matter
        me.method_calls = []

    DEBUG = 0
    indent = 0
    def _dbg_pop(  me, call): return call.name == 'PopState'
    def _dbg_push( me, call): return call.name == 'PushState'

    def play_on( me, context):
        for call in me.method_calls:
            if me.DEBUG:
                if me._dbg_pop( call): me.indent -= 1
                if me.DEBUG > 1:
                    a = raw_input( me.indent*'  ' + str(call) + ' press N to skip')
                    if a.upper() == 'N':
                        print 'skipping...', call
                        continue
                else:
                    print me.indent*'   ', call
                if me._dbg_push( call): me.indent += 1

            method = getattr( context, call.name)
            method( *call.args, **call.kargs)

    def _return( me, call):
        return None
        return str( call)

    def _record( me, name):
        def record_method_call( *a, **k):
            call = MethodCallData( name, *a, **k)
            me.method_calls.append( call)
            if me.rec_context is not None:
                #real result
                meth = getattr( me.rec_context, name)
                return meth( *a, **k)
            return me._return( call) #None
        return record_method_call

    def __getattr__( me, name):
        return me._record( name)

# vim:ts=4:sw=4:expandtab
