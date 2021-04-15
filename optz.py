# sdobrev 2010
# -*- coding: utf-8 -*-
'simple !! options-getter (wrapping optparse or else)'

_list = list
if 0:   #very simple independent ones, copy-paste from here
    #booleans/count only:
    def opt( *xx):
        n=0
        for x in xx:
            while x in sys.argv: n +=1; sys.argv.remove( x )
        return n

    #booleans only:
    def opt( *xx):
        for x in xx:
            if x in sys.argv: return sys.argv.remove( x ) or True
        return None
    o_n = opt('-n', '--dryrun')

    #booleans only:
    def opt(x):
        try: sys.argv.remove( x ); return True
        except ValueError: return None
    o_v = opt('-v') or opt('--verbose')

    # optparse simplifier/template
    import optparse
    oparser = optparse.OptionParser(
    '...')
    def optany( name, *short, **k):
        return oparser.add_option( dest=name, *(_list(short)+['--'+name.replace('_','-')] ), **k)
    def optbool( name, *short, **k):
        return optany( name, action='store_true', *short, **k)
    optbool( 'verbose', '-v')
    optany(  'outfile', '-o', help= 'outfile, "-" for stdout')
    optany(  'maxsize', '-l', type=int, help= 'max size in MBs')
    options,args = oparser.parse_args()


#more complex:  #TODO: argparse, positional, ArgumentDefaultsHelpFormatter
import optparse, sys
class OptionParser( optparse.OptionParser):
    '--ab_c=--ab-c'
    def _match_long_opt( self, opt):
        return optparse.OptionParser._match_long_opt( self, opt.replace('_','-'))

def make( *a,**k):
    global oparser
    oparser = OptionParser( *a,**k)
make()
def usage( u):  oparser.set_usage( u)
def epilog( u): oparser.epilog = u
def description( u): oparser.description = u

def optany( name, *short, **k):
    parser = k.pop( 'oparser', oparser)
    if sys.version_info[0]<3:
        h = k.pop( 'help', None)
        if h is not None:
            k['help'] = isinstance( h, unicode) and h or h.decode( 'utf8')
    return parser.add_option( dest=name, *(_list(short)+['--'+name.replace('_','-')] ), **k)
def optbool( name, *short, **k):
    return optany( name, action='store_true', *short, **k)
_int = int
def optint( name, *short, **k):
    return optany( name, type=_int, *short, **k)
_float = float
def optfloat( name, *short, **k):
    return optany( name, type=_float, *short, **k)
addopt = optany
addopt1 = addbool = optbool

def optappend( name, *short, **k):
    return optany( name, action='append', *short, **k)
def optcount( name, *short, **k):
    return optany( name, action='count', default=0, *short, **k)

def getoptz( args_in =None):
    options,args = oparser.parse_args( args_in)
    return options,args

#.. type= 'choice', choices= mp3times.apps,
_str = str

add = any = str = text = addopt
add1= bool = addbool
int = optint
float = optfloat
list = multi = append = optappend
count = optcount
get = parse = getoptz
help = usage

def group( name, **k):
    g = oparser.add_option_group( optparse.OptionGroup( oparser, name, **k))
    if not hasattr(oparser, 'options_dict'): oparser.options_dict = {}
    oparser.options_dict[ name] = g
    return g
def grouparg( name, **k):
    return dict( oparser= group( name, **k))

def iter_opt_defs(): return oparser._get_all_options()


def _allow_textfile():
    if 'textfile' not in optparse.Option.TYPES:
        optparse.Option.TYPES += ( 'textfile', )
        optparse.Option.TYPE_CHECKER.update( textfile = _check_textfile)
def _check_textfile( option, opt, value):
    try:
        return open( value ).read()
    except Exception as e:
        raise optparse.OptionValueError( 'option %(opt)s: error reading %(value)r: %(e)s' % locals())
def opttextfile( name, *short, **k):
    _allow_textfile()
    return optany( name, type= 'textfile', *short, **k)
textfile = opttextfile


if 0:
    import optz
    optz.bool( 'simvolni',  '-L',   help= 'обхожда и символни връзки')
    optz.text( 'prevodi',            help= 'речник с преводи')
    optz.append( 'etiket',   '-e',  help= 'добавя етикета към _всички описи')
    optz.count( 'podrobno',  '-v',  help= 'показва подробности', default=0)

# vim:ts=4:sw=4:expandtab
