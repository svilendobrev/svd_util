'menu description (tree) '

_TAB='  '
_level = 0

class MenuItem( object):
    id      = ''    #view/controller id/address
    label   = None
    help    = icon = ''
    is_radio = is_check = None #items only; maybe type ?
    value   = None

    address = property(             #alias for id
                    lambda me: me.id, lambda me,v: setattr( me,'id',v) )
    _aliases = [ 'address' ]
    enabled = True

    Separator = None        #this object is used AS separator

    def __init__( me, menu =None, **kargs):
        me.menu = []
        if menu: me.parse( menu)

        for k,v in kargs.iteritems():
            if k in me._aliases or k in me.__class__.__dict__ and not k.startswith('_'):
                setattr( me, k, v)
            else:
                print 'warning: invalid MenuItem arg:',k

    def append( me,v): me.menu.append( v)

    def __str__( me):
        global _level
        r = _level*_TAB + (me.menu and 'Menu' or 'Item')
        r += '( '+ ', '.join(
                        '%(k)s=%(v)r' % locals()
                            for k,v in me.__dict__.iteritems()
                            if k !='menu' ) +')'
        if me.menu:
            _level+=1
            sep = _level*_TAB+'---'
            r += '\n'+'\n'.join(
                (a is not me.Separator and str(a) or sep) for a in me.menu )
            _level-=1
        return r

    def parse( me, menuitems):
        menu = me
        klas = me.__class__
        for a in menuitems:
            if isinstance( a, klas):    #pre-cooked
                menu.append( a)
            elif isinstance( a, dict):
                menu.append( klas(**a))
            elif a is None or isinstance( a, str) and a and a.count('-')==len(a):
                "separator"
                menu.append( me.Separator )
            else:
                raise NotImplementedError, a
        return menu

Menu = Item = MenuItem

aMenu = dict
aItem = dict

#XXX ??? why here?
treemenuitems = [
                Menu(   label= '&Refresh',
                        id  = 'refresh',
                    ),
                None,
                Menu(   label= '&Add',
                        id  = 'add',
                    ),
                Menu(   label= '&Delete',
                        id  = 'delete',
                    ),
            ]

if __name__ == '__main__':
    if 10:
        aMenu = dict
        aItem = dict
    else:
        aMenu = Menu
        aItem = Item

    _mainmenu = [
    aMenu(   label = '&File',
            id   = 'file',
#                help = 'all File operations',
            menu= [
                aItem(  label= '&Save',
#                             key='ctrl-S',
                        id  = 'save',
#                            help= 'save current thing if changed',
                        icon= 'sos'
                    ),
                None,
                aItem(  label= '&Quit',
                        #key='ctrl-Q',
                        id  = 'quit',
#                            help= 'quit session',
#                            icon= 'door'
                    ),
                '-------------',
                aItem(  label= 'Open &Recent',
                        id  = 'recent files',
                        menu= [
                            aItem(  label= '&1: aFile',
                                    id  = 'file1',
                                ),
                            aItem(  label= '&2: bFileOld',
                                    id  = 'file2',
                                ),
                        ],
                    )
            ]
    ),
    aMenu(   label = '&About',
            id   = 'about',
            menu= [
                aItem(  label= '&Authors',
                        id  = 'authors',
                    ),
                aItem(  label= '&Version',
                        id  = 'ver',
                    ),
            ]
    ),
    aMenu(   label = '&Pboutsadasdasdasssssssssssssssssss',
            id   = 'about',
            menu= [
                aItem(  label= '&Authors',
                        id  = 'authors',
                    ),
                aItem(  label= '&Version',
                        id  = 'ver',
                    ),
            ]
    ),
    ]

    if 10:
        aMenu = dict
        aItem = dict
    else:
        aMenu = Menu
        aItem = Item

    m = Menu( _mainmenu)
    print m

    import sys
    if 'wx' in sys.argv:
        class Model:
            doc = 1

        from layout import Panel
        from myctl import MainController
        from wxmain import Frame

        ctl = MainController(Model)
        ctl.menu = m
        ctl.layout = Panel('@ababa\n[ doc]')
        mainf = Frame(ctl=ctl)

#    raise SystemExit,1
# vim:ts=4:sw=4:expandtab
