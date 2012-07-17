#sdobrev 2011
# -*- coding: utf-8 -*-
'html structural visitor/extractor'

from util.struct import DictAttr
dbg = 0

class HT4stack:
    #defstack = [ grammar_root]     see example at end
    stack = []
    cstack = {}

    BR_as_data = None
    nonclosables = 'br img'.split()
    #XXX not correct for tracking non-closables e.g. p or br or img, or unclosed closables e.g. div table /div
    def handle_starttag( me, tag, attrs):
        if dbg: print("11111 {tag} {attrs}".format_map( locals() ))
        if me.BR_as_data and tag =='br':
            me.handle_data( me.BR_as_data )
            return
        attrs = dict( attrs)
        if tag in me.cstack:
            me.cstack[tag].append( attrs )

        for d in me.defstack[-1]:
            if d.tag != tag:
                if dbg: print( 11222, 'adio', d.tag)
                continue
            dattrs = dict( (k[1:],v) for k,v in d.items() if k.startswith( '_') and v is not False)
            cattrs = dict( (k, v if v is True else attrs[k])
                                    for k,v in dattrs.items() if k in attrs)
            if dattrs != cattrs:
                if dbg: print( 11333, 'adio', d.tag, dattrs, cattrs)
                continue
            me.cstack.setdefault( tag, [ attrs ])
            depth = len( me.cstack[tag])
            if dbg: print( 'open', tag, dattrs, depth)
            run = d.get( 'run')
            if run: run()
            else:
                run = d.get( 'run3')
                if run: run( me, tag, attrs)
            items = d.get( 'subitems')
            if items: me.defstack.append( items)
            me.stack.append( DictAttr( org=d, attrs=attrs, data='', depth= depth))
            break
        if tag in me.nonclosables:
            me.handle_endtag( tag)

    def data2text( me, x): return x.strip()

    def handle_endtag( me, tag):
        if dbg: print("{tag} end".format_map( locals() ), len( me.cstack.get( tag,[])) )
        if tag in me.cstack:
            if me.cstack[tag]:
                me.cstack[ tag].pop()
        if not me.stack: return
        cur = me.stack[-1]
        if tag != cur.org.tag or len( me.cstack[tag])+1 != cur.depth: return
        if dbg: print( 'close', tag, cur.attrs)

        if cur.org.get( 'data'):
            data = me.data2text( cur.data)
            cur.org.data( data)
            if dbg: print("  data {data}".format_map( locals() ))

        me.stack.pop()
        if cur.org.get( 'subitems'): me.defstack.pop()
        d = me.defstack[-1][0]
        if dbg: print( "now",
            me.stack and (me.stack[-1].org.tag, me.stack[-1].attrs),
            d.tag,
            dict( (k[1:],v) for k,v in d.items() if k.startswith( '_'))
            )

    def handle_data( me, data):
        if not me.stack: return
        cur = me.stack[-1]
        if cur.org.get( 'data'):
            cur.data += data


try: from urllib.request import urlopen #p3
except: from urllib import urlopen #p2

def visit( url, stack_grammar, ienc =None, html_notfixed =False, html_strict =False, **kargs ):

    if url.startswith( 'http:'):
        u = urlopen( url)
        d = u.read()
    else:
        import io
        d = io.open( url, 'rb').read()

    if not ienc:
        import chardet  #chardet.feedparser.org, python3-chardet, python-chardet
        ienc = chardet.detect( d)[ 'encoding']   #.confidence

    if not html_notfixed:
        from util.py.parser3 import HTMLParser
    else:
        try: from html.parser import HTMLParser #p3
        except: from htmllib import HTMLParser #p2

    class HT( HT4stack, HTMLParser):
        defstack = [ stack_grammar ]

    h = HT( strict= html_strict)
    for k,v in kargs.items():
        setattr( h,k,v)
    d = d.decode( ienc )
    h.feed( d )
    h.close()
    return d


if __name__ == '__main__':

    programs_syntax = '''
    ..
      <div id="scroller-stripe">
        <div id=IGNORE class="week-day">
          <h2> Петък
            <span> (05 Август 2011)
            </span>
          </h2>
          <dl>
            <dt id=IGNORE">0:00 </dt>
            <dd id=IGNORE">Новини  </dd>
            ...
          </dl>
        </div>
        ...
    '''


    da = DictAttr

    days=[]
    def newday(): days.append( da( list= []) )
    def save_lastday_name( t): days[-1].dayname = t
    def save_lastday_date( t): days[-1].daydate = t
    def newitem(): days[-1].list.append( da() )
    def save_lastitem_time( t):  days[-1].list[-1].time = t
    def save_lastitem_title( t): days[-1].list[-1].title = t

    grammar_root= [
        da( tag= 'div', _id= "scroller-stripe", subitems=[
            da( tag= 'div', _class= "week-day", run= newday, subitems= [
                da( tag= 'h2', data= save_lastday_name, subitems= [
                    da( tag= 'span', data= save_lastday_date ),
                ]),
                da( tag= 'dl', subitems= [
                    da( tag= 'dt', run= newitem, data= save_lastitem_time ),
                    da( tag= 'dd', data= save_lastitem_title ),
                ]),
            ]),
        ])
    ]

    visit(
        'http://bnr.bg/sites/hristobotev/Pages/ProgramScheme.aspx',
        grammar_root )

# vim:ts=4:sw=4:expandtab
