#sdobrev 2006?
'source-monkey-patcher for python - extract+patch+compile a func'

def hacksrc( func, find, replace, n=1, debug =False, allow_not_found =False):
    import inspect
    module = inspect.getmodule( func)
    is_method = inspect.ismethod( func)
    owner = is_method and func.im_class or module
    src = inspect.getsource( func )
    if isinstance( find, (list,tuple)):
        assert replace is None
        items = [ (i[0],i[1],len(i)>2 and i[2] or n) for i in find ]
    else:
        items = [(find,replace,n)]

    for (find,replace,n) in items:
        #print '>>', `find`, '->', `replace`
        if n<0:     #backwards
            lines = src.split('\n')
            for i in range( len(lines)-1,0,-1):
                if find in lines[i]:
                    lines[i] = lines[i].replace( find, replace)     #first
                    break
            newsrc = '\n'.join( lines)
        else:
            newsrc = src.replace( find, replace, n)
        if not allow_not_found: assert newsrc != src
        src = newsrc

    #newsrc = ' def '+func.__name__+'(me): return 13\n'
    newsrc = newsrc.lstrip()
    if is_method:
        #newsrc = newsrc.replace( 'self.__', 'self._'+owner.__name__+'__')
        newsrc = newsrc.replace( '.__', '._'+owner.__name__+'__')
        for a in ['dict','class']:
           newsrc = newsrc.replace( '._'+owner.__name__+'__'+a+'__', '.__'+a+'__' )
    if debug: print 'hacksrc', func, 'newsrc:\n', newsrc
    def ex():
        exec newsrc in module.__dict__, locals()
        return locals()
    newfunc = ex()
    newfunc = newfunc[ func.__name__]
    setattr( owner, func.__name__, newfunc)

# vim:ts=4:sw=4:expandtab
