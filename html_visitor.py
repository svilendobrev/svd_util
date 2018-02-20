#sdobrev 2011
# -*- coding: utf-8 -*-
'html structural visitor/extractor'

from .dicts import DictAttr
from .py3 import callable
dbg = 0

class HT4stack:
    #defstack = [ grammar_root]     see example at end
    stack = []
    tstack = [] #last-to-first

    BR_as_data = None
    nonclosables = 'br img'.split()

    def check( me, dattrs, attrs):
        for k,v in dattrs.items():
            if v is False:
                if k in attrs:
                    return 201,k
                continue
            if v is True:
                if k not in attrs:
                    return 202,k
                continue
            if callable( v):
                if not v( attrs.get(k)):
                    return 203,k
            else:
                if k not in attrs:
                    return 204,k
                if v != attrs[k]:
                    return 205,k

    #XXX maybe not correct for tracking non-closables e.g. p or br or img, or unclosed closables e.g. div table /div
    autoclosables = dict(
        td = 'table tr'.split(),
        tr = 'table'.split(),
        a  = 'table tr td div'.split(),

        dt = 'dl'.split(),
        dd = 'dl'.split(),
        li = 'ul'.split(),
        p  = 'dl dt dd  table td tr  ul li'.split(),    #???
        )
    autoequivs = dict(
        dt = 'dd'.split(),
        dd = 'dt'.split(),
        )
    for k,v in autoclosables.items():
        v = autoequivs.setdefault( k, [])
        if k not in v: v.append(k)
    #nonstructural = 'b i font strong'.split()  #closing these doesnt close open structurals e.g.  b a /b

    def handle_starttag( me, tag, attrs):
        if dbg: print('-start', tag, attrs, me.tstack,
            'ld=', len(me.defstack), tuple( a.tag for a in me.defstack[-1]),
            )
        if me.BR_as_data and tag =='br':
            me.handle_data( me.BR_as_data )
            return

        parents = me.autoclosables.get( tag, ())
        equivs = me.autoequivs.get( tag, ())
        if parents or equivs:
            found = None
            tprev = None
            for t in me.tstack:
                if t == tag or t in equivs:
                    found = t
                    break
                if t in parents:
                    #found = tprev   #parent found before tag   XXX wrong to close all there
                    break
                tprev = t
            if found is not None:
                if dbg: print(" 11112 {tag} to replace [:{found}] {me.tstack} {ld}".format( ld=len(me.defstack), **locals() ))
                me.handle_endtag( found)    #all up to there
                if dbg: print(" 11113 {tag} insert {me.tstack} {ld}".format( ld=len(me.defstack), **locals() ))
        me.tstack.insert( 0,tag)

        attrs = dict( (k,v if not v else v.strip()) for k,v in attrs )  #no hanging spaces plz

        for d in me.defstack[-1]:
            if d.tag != tag:
                if dbg: print( ' 11222 skip', d.tag)
                continue

            #'prepend any attr for filtering with _'
            dattrs = dict( (k[1:],v) for k,v in d.items() if k[0]== '_')
            c = me.check( dattrs, attrs)
            if c:
                if dbg: print( c[0], 'adio', d.tag, c[1], dattrs, attrs)
                continue

            depth = len( me.tstack)
            if dbg: print( 'open', tag, dattrs, depth)
            run = d.get( 'run')
            if run:
                if dbg: print( 'run', tag, attrs, depth)
                run()
            else:
                run = d.get( 'run3')
                if run:
                    if dbg: print( 'run3', tag, attrs, depth)
                    run( me, tag, attrs)
            items = d.get( 'subitems')
            if items: me.defstack.append( items)
            me.stack.append( DictAttr( org=d, attrs=attrs, data='', depth= depth))
            #cur = me.stack[-1]
            if dbg: print('-started', tag, me.tstack,
                'ld=', len(me.defstack), tuple( a.tag for a in me.defstack[-1]),
                )
            break
        if tag in me.nonclosables:
            me.handle_endtag( tag)

    def data2text( me, x): return x.strip()

    def handle_endtag( me, tag):
        if dbg: print('-end', tag, me.tstack, #me.stack,
            'ld=', len(me.defstack), tuple( a.tag for a in me.defstack[-1]),
            )

        len_tstack = len( me.tstack)    #with
        if tag in me.tstack:
            ix = me.tstack.index( tag)
            for t in me.tstack[:ix]:
                me.handle_endtag( t)
            assert len( me.tstack)+ix == len_tstack
            assert me.tstack[0] == tag
            len_tstack = len(me.tstack) #with
            me.tstack.pop(0)

        if not me.stack: return
        cur = me.stack[-1]
        if dbg: print(' ',3333, tag, 'lt=', len_tstack, cur)
        if tag != cur.org.tag or len_tstack != cur.depth: return
        if dbg: print( 'close', tag, cur.attrs)

        if cur.org.get( 'data'):
            data = me.data2text( cur.data)
            cur.org.data( data)
            if dbg: print("  data {data}".format_map( locals() ))

        me.stack.pop()
        if cur.org.get( 'subitems'): me.defstack.pop()
        if dbg: print( "-now", me.tstack,
            'ld=', len(me.defstack), tuple( a.tag for a in me.defstack[-1]),
            me.stack[-1:],
            )

    def handle_data( me, data):
        if not me.stack: return
        cur = me.stack[-1]
        if cur.org.get( 'data'):
            cur.data += data


try: from urllib.request import urlopen #p3
except: from urllib import urlopen #p2

def visit( url, stack_grammar, ienc =None, html_notfixed =False, html_strict =False,
            return_also_headers =False,
            **kargs ):
    u = None
    if url.startswith( 'http:'):
        try:
            u = urlopen( url)
            d = u.read()
        except:
            print( '????:', url)
            raise
    else:
        import io
        d = io.open( url, 'rb').read()

    if not ienc:
        import chardet  #chardet.feedparser.org, python3-chardet, python-chardet
        ienc = chardet.detect( d)[ 'encoding']   #.confidence

    if not html_notfixed:
        from .py.parser3 import HTMLParser
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
    if return_also_headers: return d, u and u.get_headers()
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
