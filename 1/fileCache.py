#$Id: fileCache.py,v 1.8 2006-07-12 11:24:39 sdobrev Exp $
#s.dobrev 2k3-4

#could use linecache.getlines() - has checkcache() / updatecache(),
#   but it looks on sys.path, and returns list.
#so, DIY

class FileCache:
    def __init__( me):
        me.cache = {}
    def read( me, f_name):  #generator?
        try:
            content = me.cache[ f_name]
        except KeyError:
            content = None
            f = file( f_name, 'r')
            try:
                content = me.cache[ f_name] = f.read()
            finally:
                f.close()
        return content

##############

class Descriptor4FileCachedLazyAsText( object):
    attrname = None #'some_hidden_attr_name'
    process_firsttime = None    #(obj,result)
    def __init__( me, filename, attrname =None, process_firsttime =None):
        me.filename = filename
        if attrname is not None: me.attrname = attrname
        if process_firsttime is not None: me.process_firsttime = process_firsttime
        assert me.attrname
    def __get__( me, obj, klas):
        attrname = me.attrname
        try: r = getattr( obj, attrname)
        except AttributeError:
            filename = me.filename
            try:
                f = open( filename)
                try: r = f.read()
                finally: f.close()
            except IOError:
                print '! can`t read file', filename
                r = ''
            pr = me.process_firsttime
            if pr: r = pr( obj, r)
            setattr( obj, attrname, r)
        return r

# vim:ts=4:sw=4:expandtab
