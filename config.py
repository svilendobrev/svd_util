# ~2007 s.dobrev h.stanev
'hierarchical namespaced configuration language, with types and helps and inheritance'

import sys

GLOBAL_NAMESPACE = ''

class NamespaceDispatcher( object):
    def __init__( me):
        me.namespaces = {}
        me.consumed_args = set()

    def register( me, cfg):
        nms = me.namespaces.setdefault( cfg._prefix, {})
        nms.update( cfg._get_default_values())
        return nms

    def dispatch( me, attr_name, cfg):
        prefix, name = cfg.prefix_and_name( attr_name)
        prefix = prefix != GLOBAL_NAMESPACE and (prefix, GLOBAL_NAMESPACE) or (prefix,)
        for pfx in prefix:
            try: return me.namespaces[ pfx ][ name]
            except KeyError: pass
        me._attr_error( attr_name)

    def update( me, attr_name, value, cfg):
        pfx, name = cfg.prefix_and_name( attr_name)
        try:
            nms = me.namespaces[ pfx ]
        except keyerror:
            me._attr_error( attr_name)
        else:
            nms[ name ] = value

    def _attr_error( me, attr_name):
        print 'CONFIG ERROR: unknown config variable %(attr_name)s' % locals()
        raise AttributeError

_pfx_sep = '.'

_disp = NamespaceDispatcher()

_help_sep = '::'

_list_conv = lambda val: val.split(',')


def _config_defaults( cfg):
    return dict( (k,v) for k,v in dir( cfg) if not k.startswith('_') and not callable( v))


def _is_config_data( name, value =None):
    return not name.startswith('_') and not callable( value)


class _ConfigMeta( type):
    ''' adds inheritance for _help;
    prevents from losing parent's settings if the parent was not inited at all'''
    def __init__( cls, name, bases, dct):
        cls._help = '\n'.join( [ getattr( b, '_help', '') for b in [ cls ] + list(bases) ] )

class ConfigBase( object):
    ''' namespace or part of such forming the whole config data. used as interface to other namespaces.
        config variables should not start with '_'
    '''
    __metaclass__ = _ConfigMeta
    _all_instances = []
    _prefix = GLOBAL_NAMESPACE
    _remove_from_argv = True #False
    _enable_type_conversion = True

    _type_conv = {
        list  : _list_conv,
        tuple : _list_conv,
    }

    def __init__( me, *ignored):
        me._namespace = _disp.register( me)
        me._all_instances.append( me)

    def _get_default_values( me):
        klas = me.__class__
        res = {}
        for name in dir( klas): #XXX don't use vars() as it doesn't include parent's attribs
            v = getattr( klas, name)
            if name.startswith('_') or callable( v): continue
            res[ name] = v
        return res


    def __getattribute__( me, name): # FIXME use a descriptor
        ''' hides class variables and thus lets the dispatcher take control'''
        res = object.__getattribute__( me, name)
        if _is_config_data( name, res):
            return _disp.dispatch( name, me)
        return res

    def __getattr__( me, name):
        if _is_config_data( name):
            return _disp.dispatch( name, me)
        return object.__getattr__( me, name)

    def __setattribute__( me, name, value): # FIXME use a descriptor
        ''' hides class variables and thus lets the dispatcher take control'''
        if _is_config_data( name):
            return _disp.update( name, value, me)
        return object.__setattribute__( me, name, value)

    def __setattr__( me, name, value):
        if _is_config_data( name):
            return _disp.update( name, value, me)
        return object.__setattr__( me, name, value)

    def getopt( me, help =None):
        for h in ['help', '-h', '--help']:
            if h in sys.argv:
                print help or me.allhelp()
                print me
                raise SystemExit, 1

        for c in reversed(me._all_instances):
            c._getopt( help)

        try: sys.argv.remove( 'cfg_warning')
        except ValueError: pass
        else:
            for a in set(sys.argv) - _disp.consumed_args:  #what's left
                print '!cfg: ignoring arg', a

    def prefix_and_name( me, attr_name, default_prefix =None):
        if default_prefix is None:
            default_prefix = me._prefix
        return _pfx_sep in attr_name and attr_name.split( _pfx_sep) or ( default_prefix, attr_name)

    def _getopt( me, help =None):
        myhelp = help or me._help
        possible_args = set( [ ak.strip().split()[-1] for ak in myhelp.split( _help_sep)[:-1]] )
        assert possible_args, me.__class__.__name__ + ''':empty help?? - syntax is
boolname    :: text.. for positive booleans
no_boolname :: text.. for negative booleans
valuename=  :: text.. for name=value
where boolname and valuename are the attributes of the class
'''
        for expr in sys.argv[1:]:
            arg_val = expr.split('=')
            prefixed_name = arg_val[0]
            pfx, name = me.prefix_and_name( prefixed_name, '')
            if pfx != me._prefix: continue
            if len(arg_val) < 2:
                if name in possible_args:
                    if name.startswith('no_'):
                        name = name[3:]
                        v = False
                    else:
                        v = True
                    me._set_value( name, v, name)
            else:
                if name+'=' in possible_args:
                    val = '='.join( arg_val[1:])   #XXX working in case >= 2 = like "db=sapdb:///sap?kliuche=abdahalia"
                    if me._enable_type_conversion:
                        myval = getattr( me.__class__, name, None)
                        if myval is not None:
                            typ = type( myval)
                            try:
                                val = me._type_conv.get( typ, typ)( val)#XXX bool won't work, bool('False') == True
                            except ValueError:
                                continue
                    me._set_value( name, val, expr)

    def _set_value( me, name, val, consumed):
        if me._remove_from_argv:
            try:
                sys.argv.remove( consumed)
            except ValueError:
                pass
        _disp.consumed_args.add( consumed)
        me._namespace[ name ] = val

    def allhelp( me):
        'ignoring duplicate entries; first is used'
        h = ''
        for c in me._all_instances:
            try: h += c._help
            except AttributeError: pass

        ikeys = []
        out = []
        ikey = item = ''

        def add( ikey,item):
            ik = ikey.strip()
            if ik and ik not in ikeys and ik+'=' not in ikeys:
                ikeys.append( ik)
                out.append( _help_sep.join( (ikey,item) ))

        for l in h.split('\n'):
            ischapter = not l.startswith(' ')
            if _help_sep in l or ischapter:
                add( ikey,item)
                if ischapter:
                    out.append( l)
                    ikey,item = '',''
                else:
                    ikey,item = l.split( _help_sep)
            else:
                item += '\n'+l
        add( ikey,item)
        return '\n'.join(out)

    def __str__( me):
        namespaces = _disp.namespaces.copy()
        nmspace_txt = lambda pfx: (pfx==GLOBAL_NAMESPACE and 'global namespace' or pfx)
        s = 'current namespace: %s\n' % nmspace_txt( me._prefix)
        for prefix, namespace in sorted( namespaces.iteritems(), key= lambda (x,y): x):
            s += '------- %s --------\n' % nmspace_txt( prefix)
            s += '\n'.join( [ '%s=%s' % (k,str(v)) for k,v in sorted( namespace.iteritems(), key= lambda (x,y): x) ]) + '\n'
        return s


#############################################

class ConfigOld:
    def __init__( me, *chain):
        me._chain = list(chain)
    def __getattr__( me, a):
        for c in me._chain:
            try: return getattr( c, a)
            except AttributeError: pass
        raise AttributeError

    def __str__( me):
        all = set( dir(me) )
        for c in me._chain:
            all = all | set( dir( c))
        all = sorted( all)
        return ', '.join( '%s=%s' % (k,getattr(me,k))
                    for k in all
                    if not k.startswith('_') and not callable( getattr(me,k))
                )

    def allhelp( me):
        'ignoring duplicate entries; first is used'
        h = ''
        chain = [ me ] + me._chain
        for c in chain:
            try: h += c._help
            except AttributeError: pass

        ikeys = []
        out = []
        ikey = item = ''

        def add( ikey,item):
            ik = ikey.strip()
            if ik and ik not in ikeys and ik+'=' not in ikeys:
                ikeys.append( ik)
                out.append( '::'.join( (ikey,item) ))

        for l in h.split('\n'):
            ischapter = not l.startswith(' ')
            if '::' in l or ischapter:
                add( ikey,item)
                if ischapter:
                    out.append( l)
                    ikey,item = '',''
                else:
                    ikey,item = l.split('::')
            else:
                item += '\n'+l
        add( ikey,item)
        return '\n'.join(out)

    def getopt( me, help =None):
#        if help is None and not use_own: help = me.allhelp() #_help
        for h in ['help', '-h', '--help']:
            if h in sys.argv:
                print help or me.allhelp()
                print me
                raise SystemExit, 1

        me._getopt( help)

        try: sys.argv.remove( 'cfg_warning')
        except ValueError: pass
        else:
            for a in sys.argv:  #what's left
                print '!cfg: ignoring arg', a

    def _getopt( me, help =None, use_own =None):
        if use_own is None: use_own = me._chain
        myhelp = help
        if use_own: myhelp = me._help
        possible_args = [ak.strip().split()[-1] for ak in myhelp.split('::')[:-1]]
        for a in sys.argv[1:]:
            aa = a.split('=')
            if len(aa)<2:
                if a in possible_args:
                    sys.argv.remove( a)
                    if a.startswith('no_'):
                        a = a[3:]
                        v = False
                    else: v = True
                    setattr( me, a, v)
            else:
                k = aa[0]
                if k+'=' in possible_args:
                    sys.argv.remove( a)
                    val = '='.join( aa[1:])   #XXX working in case >= 2 = like "db=sapdb:///sap?kliuche=abdahalia"
                    uselist = isinstance( getattr( me.__class__, k, ''), (list,tuple) )
                    if uselist:
                        val = val.split(',')
                    setattr( me, k, val)

        for c in me._chain:
            c._getopt( help, use_own)    #having _chain and not use_own ... useless - argv is empty


if 1:
    Config = ConfigBase
else:
    Config = ConfigOld

Config.Config = Config  #easy available as cfg.Config, instead of cfg.__base__[0].__class__...


if 0:
    from sqlalchemy.util import OrderedSet
    class ConfigDispatcher( NamespaceDispatcher):
        def __init__( me):
            NamespaceDispatcher.__init__( me)
            me._checked = None

        def register( me, cfg):
            nms = me.namespaces.setdefault( cfg._prefix, OrderedSet())
            nms.add( cfg)

        def dispatch( me, attr_name, checked):
            if me._checked: raise AttributeError # stop recursion
            me._checked = checked
            pfx, name = me.sep in attr_name and attr_name.split( me.sep) or ( checked._prefix, attr_name)
            nms = me.namespaces.get( pfx)
            if nms:
                for cfg in reversed( nms - set( [ me._checked ])):
                    try:
                        res = getattr( cfg, name)
                    except AttributeError:
                        pass
                    else:
                        me._checked = None
                        return res # success
            me._checked = None
            me._attr_error( attr_name)


if __name__ == '__main__':
    Config = ConfigBase
    class sys:
        argv = None

    import unittest

    class C0( ConfigBase):
        n = 1
        alabala = True
        l = 'a b c'.split()
        overridden = 10
        _help = '''
    no_alabala :: bool
    n= :: int
    l= :: list
    overridden  :: overridden'''

    class C1( C0):
        _prefix = 'nms1'

    class C2( C1):
        m = 2
        overridden = 15

        _help = '''
    no_alabala  :: bool
    x=          :: int'''

    class C3( C2): # different namespace
        _prefix = 'nms2'

    def getopt( cmd, cfg):
        sys.argv = cmd.split()
        cfg.getopt()

    class SimplestCase( unittest.TestCase):
        def setUp( me):
            global _disp
            _disp = NamespaceDispatcher()
            me.config = C0()

        def test_defaults( me):
            getopt( 'ignored n=5 x=10', me.config)
            me.assertEqual( me.config.n, 5)
            me.assertRaises( AttributeError, lambda: me.config.x)

            getopt('ignored n=10 x=10', me.config)
            me.assertEqual( me.config.n, 10, 'config update error')
            me.assertEqual( me.config.l, 'a b c'.split())
            me.assertRaises( AttributeError, lambda: me.config.ignored)
            me.assertRaises( AttributeError, lambda: me.config.x)

        def test_list_value( me):
            getopt('ignored n=1,2,3 l=3,4,5 x=5,6,7', me.config)
            me.assertEqual( me.config.n, 1, 'attr type changed')
            me.assertEqual( me.config.l, '3 4 5'.split(), 'list error')
            me.assertRaises( AttributeError, lambda: me.config.x)

        def test_bool_value( me):
            getopt('ignored no_alabala', me.config)
            me.assertEqual( me.config.alabala, False, 'bool error')

        def tearDown( me):
            global _disp
            del _disp


    class DistributedSingleNamespaceCase( SimplestCase):
        def setUp( me):
            SimplestCase.setUp(me)
            me.c0 = me.config
            me.c1 = C1()
            me.c2 = C2()
            getopt('ignored nms1.n=5 nms1.x=10 nms2.no_alabala unknown=500 nms1.unknown=600 nms2.unknown=700', me.c1)

        def check_common_values( me, cfg, pfx =''):
            if pfx: pfx += _pfx_sep
            get = lambda name: getattr( cfg, pfx+name)
            me.assertEqual( get('n'), 5)
            me.assertRaises( AttributeError, lambda: get('ZZZ'))
            me.assertRaises( AttributeError, lambda: get('unknown'))
            me.assertRaises( AttributeError, lambda: get('ignored'))

        def test_common_values( me):
            me.check_common_values( me.c1, pfx=me.c1._prefix)
            me.check_common_values( me.c2, pfx=me.c2._prefix)
            me.assertEqual( me.c1.alabala, True)
            me.assertEqual( me.c2.alabala, True)

        def test_load_priority( me):
            me.assertEqual( me.c1.overridden, 15, 'FIXME: overriding not implemented')
            me.assertEqual( me.c1.overridden, me.c2.overridden)


    class MultipleNamespaces( DistributedSingleNamespaceCase):
        def setUp( me):
            DistributedSingleNamespaceCase.setUp( me)
            me.c3 = C3()
            getopt('ignored nms1.n=5 nms1.x=10 unknown=500 nms1.unknown=600 nms2.unknown=700 nms2.no_alabala', me.c3)

        def test_common_values( me):
            DistributedSingleNamespaceCase.test_common_values( me)
            me.check_common_values( me.c3, me.c1._prefix) # accessing foreign namespace
            me.assertEqual( me.c3.alabala, getattr( me.c3, 'nms2.alabala'))

    '''TODO add tests for:
        setting/getting a config value at any time, not just by getopt() and not only in the config's default namespace;
        setting/getting a non config value - attr name starting with '_'
        types matching - try to set a bool value to an integer attribute
        overlapping configs in a common namespace
        namespace relations - local namespace and the global namespace
        multiple inheritance - not supported yet
        etc
    '''

    unittest.main()



# vim:ts=4:sw=4:expandtab
