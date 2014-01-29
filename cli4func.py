#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Svilen Dobrev, 2014

import argparse, inspect

def _get_subactions_sorted( me):
    return sorted( me._choices_actions, key= lambda x: x.dest)
argparse._SubParsersAction._get_subactions = _get_subactions_sorted

class CLI(object):
    '''wrap plain python funcs into command-line-interface of subcommands, with arguments.
        infer the arguments position-or-option/type/optionality/varargs from plain default values, and/or extra description.
        functions are untouched, i.e. usable from inside python.
    '''
    def __init__( me, **ka):
        me.parser = argparse.ArgumentParser( **ka)
        me.subparsers = me.parser.add_subparsers(
            description = None,     #hack to force per-command help
            metavar = '',           #hack for nicer help
            title = 'subcommands ("%s <subcommand> --help" for usage)' % me.parser.prog ,
            )

    def infer( me, func, common_args ={} ):
        'args = dict( argpyname : dict( arg-attributes ) )'
        common_args = common_args or {}
        spec = inspect.getargspec( func)
        defaults = dict( zip( *[reversed(a) for a in ( spec.args, spec.defaults or ())] ))

        result = []
        #optpos = {}
        def add_arg( name, positional =False, **ka):
            #cant have non-optional positional after optional, or any after */+ TODO
            #nargs = ka.get('nargs')
            #previous = list( optpos.items()) #get( '*') or optpos.get( '?'
            #if previous:
            #    previous = previous[0]
            #    if previous
            #        assert previous[0] '*' not in optpos and '?' not in optpos, (a,ka)
            #if nargs:
            #    optpos[ nargs] = (a,ka)

            if not positional: name = '--'+name
            result.append( ((name,),ka) )

        for k in spec.args:
            if k[0]=='_': continue  #means: internal argument: ignore
            ka = dict( positional =True)
            inkargs = common_args.get( k, {})
            if k in defaults:
                v = defaults[k]
                k,kw = me._infer_arg( k,v, positional= inkargs.pop( 'positional', False) )
                ka.update(kw)
            ka.update( inkargs)    #override auto from defaults
            add_arg( k, **ka )

        if spec.varargs:    #means: all further positionals ; add AFTER all other args
            ka = dict( nargs= '*' ) #argparse.REMAINDER ?
            ka.update( common_args.get( spec.varargs, {}))     #may override nargs

            if spec.varargs.endswith('s'): #plural
                ka.update( metavar= spec.varargs[:-1] )
                choices = ka.get( 'choices')
                if choices:     #fix argparse: it loses the choices in help with metavar
                    ka.update( help= (ka.get('help') or '') + '; one of '+','.join( choices))
            print 444, spec.varargs, ka
            add_arg( spec.varargs, positional= True, **ka)

        return result

    def _infer_arg( me, k, v, positional =False, autorename =True):
        ka = dict( positional= positional)
        if v is False:      #means: optional normal boolean, df=False
            ka.update( action= 'store_true')
        elif v is True:     #means: optional reverted boolean, df=True .. reverse-option
            ka.update( action= 'store_false', default= True, dest= k)
            if autorename and not k.lower().startswith('no_'):
                k = 'no-'+k     #??? XXX .. only the option, not the .dest
        else:
            ka.update( default= v)
            if positional:   #means: optional positional
                ka.update( nargs='?')
            else:
                if v is not None:
                    ka.update( type= type(v) )
        return k,ka

    def add_global_option_auto( me, k, v, **ka):
        k,ka = me._infer_arg( k,v, **ka)
        assert not ka.pop( 'positional', False)
        me.parser.add_argument( '--'+k, **ka)
        return k

    def add_command( me, func, args =(), name =None, help =None ):
        'args = [ (a,ka) ] for add_argument( *a, **ka) direct'
        subp = me.subparsers.add_parser( name or func.__name__,
                            help= help or getattr( func, '__doc__', None) or '',
                            )
        subp.set_defaults( _func= func)
        for a,kw in args:
            subp.add_argument( *a,**kw)


    def command( me, func =None, args =(), **ka):
        'decorator; args = [ (a,ka) ] for add_argument( *a, **ka) direct'
        def wrapper( func ):
            me.add_command( func, args= args, **ka)
            return func
        if not func: return wrapper
        return wrapper( func)

    def command_auto( me, func =None, common_args ={}, **ka):
        'decorator; common_args = dict( argpyname : dict( arg-attributes ) )'
        def wrapper( func ):
            args = me.infer( func, common_args= common_args)
            me.add_command( func, args= args, **ka)
            return func
        if not func: return wrapper
        return wrapper( func)

    def run( me, namespace_from_parse_args =None, args= None):
        'runner.. use alone, or after grabbing other args, pass namespace_from_parse_args'
        namespace = namespace_from_parse_args
        if namespace is None:
            namespace = me.parser.parse_args( args)     #args+sys.argv -> Namespace
        a  = namespace._get_args()      #always empty ..
        ka = dict( namespace.__dict__ )
        func = ka.pop( '_func')

        #move varargs as *varargs
        spec = inspect.getargspec( func)
        if spec.varargs:
            #XXX varargs cant work if any other positionals - which are named into ka.
            #should convert them back into args, remove from ka
            #hack : convert *all* into args
            allargs = [ ka.pop( k) for k in spec.args ]
            varargs = ka.pop( spec.varargs)
            a = allargs + varargs + a     #??

        if me.debug: print( func, a, ka, spec)
        return func( *a,**ka)

    debug = False

if __name__ == '__main__':
    m = Cli()
    m.debug = 1

    @m.command_auto
    def b( pos1, opt_None =None, opt_str ='', opt_false =False, opt_true =True, *pos_varargs):
        print dict( locals())

    @m.command_auto( common_args= dict(
        pos1_opt= dict( positional=True),
        pos2_opt= dict( positional=True),
        ))
    def c( pos1_opt =None, pos2_opt =None):
        print dict( locals())

    @m.command_auto
    def d( pos_opt =None, *pos_varargs):
        print dict( locals())

    #r = m.run( 'f'
    m.run()
# vim:ts=4:sw=4:expandtab
