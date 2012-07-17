#$Id$

import re
_re_karg_parse = re.compile( '^(\w+)=(.*)$' )

def parse_args( sysargv, only_kargs =False):
    # sort of eval( ','join( re.subst( '((\w+)=)?(.*)', \1'\2', sysargv)) )
    # e.g. a1 b2 c3=v5 d4=v6 -> ['a1','b2'], { 'c3':'v5', 'd4':'v6' }
    args = []
    kargs = {}
    for a in sysargv:
        m = _re_karg_parse.match( a)
        if m:
            kargs[ m.group(1) ] = m.group(2)
        else:
            if only_kargs:
                raise SyntaxError, 'only keyword args allowed: '+ str(sysargv)
            elif not kargs:
                args.append( a)
            else:
                raise SyntaxError, 'non-keyword arg after keyword-arg: '+ str(sysargv)
    return args, kargs


def help_kargs( kargs, ignore =['help'] ):
    l = kargs.items()    #copy
    l.sort()
    return ', '.join( [ '%s=%r' % item for item in l if item[0] not in ignore ] )

def _helper( run):
    run( help=True)
    raise SystemExit, 1

def runner( run, only_kargs =True, allow_no_arguments =False):
    import sys
    try:
        args,kargs = parse_args( sys.argv[1:], only_kargs=only_kargs)
    except SyntaxError:
        import traceback
        traceback.print_exc()
        return _helper( run)

    if not args and not kargs:
        if not allow_no_arguments:
            print ' needs at least one argument'
            return _helper( run)

    try:
        return run( *args, **kargs )
    except TypeError:
        import traceback
        traceback.print_exc()
        return _helper( run)

_trues = ('True', 'true')
def boolean( value, trues =_trues):
    if isinstance( value, str): value = (value in trues)
    return value

if __name__ == '__main__':

    def run(
            ip ='',
            root ='',
            http_port  =None,
            https_port =None, https_keys_path ='<default>',
            bool_flag =True,

            help =False,
        ):
        print 'use:', help_kargs( locals() )
        if help:
            return
        if isinstance( bool_flag, str): bool_flag= (bool_flag== 'True')
        #other booleans here!
        print 'boolean bool_flag is', repr(bool_flag)

        print '\nwell, do something here\n'


    runner( run)

# vim:ts=4:sw=4:expandtab
