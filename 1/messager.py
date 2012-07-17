#$Id: messager.py,v 1.4 2004-06-02 17:19:41 sdobrev Exp $

from str import str_args_kargs

class Message:      #maybe slots etc
    def __init__( me,
            format   =None,
            category =None,
            #messager =None,
        ):
        #me.messager = messager  #bound or unbound, bound ones may self-destroy!
        me.category = category
        me.format = format

    def _print( me, messager, func, args, kargs):
        #messager = me.messager
        #print 'got %r %r for %r, %r' % (args, kargs, me.format, messager)
        if messager:
            if me.format:
                out = me.format % (args or kargs or ())
                me.format = None    #once only
            else:
                out = str_args_kargs( _delimiter=' ', *args,**kargs)
            messager._message( out, me.category)
            me.category = None       #once only
        return func

    def to( me, messager):      #bind
        m = Message( category=me.category, format=me.format)    #messager=messager,
        def prn( *a,**k): return m._print( messager, prn, a,k)  #hackish ;-) - leaves 'me' free!
        return prn

class MessageLevel( Message):
    cWARNING = '! warning'
    cERROR   = '!!! error'
    LEVEL    = 0
    def __init__( me,
            format   =None,
            level    =LEVEL,
            category =None,         #none is auto-by-level
            **kargs ):
        me.level = level
        if category is None:
            category = level>me.LEVEL and me.cWARNING or me.cERROR
        Message.__init__( me, format=format, category=category, **kargs)

    def to( me, messager):      #bind
        if messager and not messager.is_visible( me.level):
            messager = None     #off
        return Message.to( me, messager)
    def is_error( me): return me.category == me.cERROR

    def Warning( klas, format, level =LEVEL+1, category =None):
        return klas( format=format, level=level, category=category)
    def Error( klas, format, category =None):
        return klas( format=format, level=klas.LEVEL, category=category)
    Warning = classmethod( Warning)
    Error = classmethod( Error)



class MessagePrinter:
    prefix = ' '
    suffix = ':'
    level = 1

    def __init__( me,
            default_category ='',
            default_level =0,
            state =True,                #True =all on; False =all off, None =auto-by-level
            level =1
        ):
        me.default_message = MessageLevel( category=default_category, level=default_level)
        me.state = state
        me.level = level

    def set_state( me, all ):               #True =all on; False =all off, None =auto-by-level
        state = me.state
        me.state = all
        return state
    def all_on( me):        return me.set_state( True)
    def all_off( me):       return me.set_state( False)
    def auto_by_level( me): return me.set_state( None)
    def is_visible( me, level ):
        if me.state is None:
            return me.level >= level
        return me.state
    def __str__( me):
        return '%s( show %s)' % (me.__class__.__name__,
            me.state is None and ('level %d and below' % me.level)
                              or ('all '+ (me.state and 'on' or 'off'))
            )

    def __call__( me, *args,**kargs ):
        if args and isinstance( args[0], Message):
            return args[0].to( me)  #ignore all other!
        return me.default_message.to( me)( *args, **kargs)
    message = __call__

    def _message( me, message, category):
        if category:
            message = me.prefix+ category +me.suffix + ' ' + message
        me._use_message( message)
        return message
    def _use_message( me, message):
        print message


if __name__ == '__main__':
    justmssg = Message( category='note' )
    levelmsg = MessageLevel( format='aide de %s', category='annoYer', )
    warn1    = MessageLevel.Warning( 'alabala %(name)s', level=5)
    error1   = MessageLevel.Error( 'abe hey %s' )

    def t( messager):
        print messager
        messager( 'just some text' )
        messager( 'the args are:', arg1=1, arg2=2)( 'and also:', boza='golema')
        messager( warn1)( name='portokale' )
        messager( warn1)( name='portokale2' )( 'and also:', boza='golema2')
        #messager( warn1(  name='portokale3' )( 'and also:', boza='golema3') )
        justmssg.to( messager)( 'portokala', 'olle', me='az',a=4,k=6  )
        error1.to( messager)( 'portokala' )
        messager( MessageLevel( category='YELL', level=2 ))( 'the args are:', arg1=1, arg2=2 )
        print '-------'


    messager= MessagePrinter()
    t(messager)
    messager.auto_by_level()
    messager.level = 0
    t(messager)

# vim:ts=4:sw=4:expandtab
