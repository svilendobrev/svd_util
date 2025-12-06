#sdobrev 2010
'xml into object, multi-language values'

if 0*'amara':
    #import amara           # XML binding toolkit
    def parse( t):
        r = amara.parse( t)
        return r.getroot()

elif 0*'lxml':
    #rough idea - not working
    from lxml import objectify
    class X:pass
    def parse( t):
        r = objectify.fromstring( t)
        X.PTVResponse = r
        return X

else: #ElementTree - ok
    from dicts import DictAttr
    #import sys
    class e3obj( DictAttr):
        def __str__( me): return me._text__
        def __init__( me, e3):
            DictAttr.__init__( me, _text__= e3.text or '', **e3.attrib)
            for i in e3:
                tag = i.tag.rsplit('}',1)[-1]
                if tag in me:
                    ii = me[ tag]
                    if not isinstance( ii, list):
                        ii = me[ tag] = [ ii ]
                    ii.append( e3obj( i))
                else:
                    me[ tag] = e3obj( i)
            #print >>sys.stderr, me.keys()

    import xml.etree.cElementTree as et
    def parse( t):
        t = unicode(t,'utf-8')
        try:
            t = t.encode('utf-8')
        except UnicodeDecodeError, e:
            print e, e.start, e.end, t[ e.start-10 : e.end+10]
            raise
        if t.lstrip().startswith( '<'):
            q = et.fromstring( t)
        else:
            q = et.parse( t).getroot()
        r = e3obj( q)
        return r#DictAttr( PTVResponse= r)
    def iterable( t):
        if t is None: return ()
        return not isinstance( t, (list,tuple)) and (t,) or t

def get_from_langdict_any( v, lang):
    if isinstance( v, dict) and '_text__' in v:    #single, direct from xml2obj #XXX HACK
        v = [v]
    if not isinstance( v, dict):    #list, direct from xml2obj
        v = dict_lang_text_from_itemlist( v)
    #else preproc
    return get_from_langdict( v, lang)

def dict_lang_text_from_itemlist( item):
    return dict( (n.lang, unicode(n)) for n in iterable( item))
def dict_lang_textlist_from_itemlist( item):
    r = {}
    for n in iterable( item):
        r.setdefault( n.lang, []).append( unicode(n))
    return r

def get_from_langdict( v, lang):
    if not v: return None
    return v.get( lang) or v.get( 'und') or (v and v.values()[0] or None)    #maybe for undefined

truefalse = dict( true=True, false= False)

# vim:ts=4:sw=4:expandtab
