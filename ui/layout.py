#s.dobrev 2k3-9
'language for dialog/form layout description - parser & buider'

import re

grammar = """
row  = (item)* | '@' panel_title
item = field | outside
field = t_input | t_buton | t_label
t_input  = '[' flags_input entry ']'
t_buton  = '<' flags_buton entry '>'
t_label  = '{' flags_label entry '}'
entry  = name | ''
flags_input = i_subtype | flags
i_subtype = i_checkbox | i_text | i_chooser
i_checkbox = '_'|'X'
i_text     = ' '|'T'
i_chooser  = '?'|'C'
flags_buton = flags
flags_label = flags
flags = mark | extender | empty
empty = '@'
extender = '+'
"""
#mark  = '!'

#empty field (no flags, no entry) can be used as column separator
#field with empty flag makes empty column (nothing in it),
# but attributes can be set via entry-name

from util.attr import Struct

class TokenMap( Struct):
    __slots__ = [ '_reversed']
    def __init__( me, **k ):
        Struct.__init__( me, **k )
        d = {}
        for key,v in k.iteritems():
            d[v] = key
        me._reversed= d
    def join_tokens( me, s):
        return s.join( me.__dict__.itervalues() )

field_types = [ '[input]', '<button>', '{label}', ]
input_types = TokenMap( Checkbox= '_', Text ='', Chooser ='?' ) #'' is default
flags = TokenMap( extend= '+', empty= '@' ) #mark= '!',


from fielddata import FieldData, ChooserFieldData, FieldUndefinedError

class Field:
    def __init__( me, name =None, typ =None,
                    flags ='', pos =0, width =0, height =1,
                    subtyp ='', _extender =None, fielddata =None):
        me.name = name
        me.typ  = typ
        me.subtyp = subtyp
        me.pos  = pos
        me.width= width
        me.height= height
        me.flags= flags
        me._extender = _extender
        #if not fielddata: fielddata = {}
        me.fielddata = fielddata
        #me.__dict__.update( k)
    def setup( me, fielddata =None):
        if not me._extender:
            if me.typ=='input':        #subparser-flags
                if not me.subtyp:
                    for flag in me.flags:
                        try:
                            me.subtyp = input_types._reversed[ flag]
                        except KeyError: pass
                        else:
                            me.flags = me.flags.replace( flag,'',1)
                            break
                if not me.subtyp:
                    me.subtyp = input_types._reversed[ '']
            if fielddata:
                me.fielddata = fielddata        #or update?
    def getFieldData( me):
        factory = me.subtyp == 'Chooser' and ChooserFieldData or FieldData
        fielddata = factory( me.name, width=me.width, height=me.height, pos=me.pos)
        #if me.typ == 'input':
        #    fielddata.label = fielddata.label + ':'
        if me.fielddata:
            fielddata.setup( **me.fielddata)
        fielddata.factory = me.getType()
        return fielddata
    def __str__( me):
        r = '%(pos)3d: %(typ)s' % me.__dict__
        if me.subtyp:
            r += '-%(subtyp)s' % me.__dict__
        r += ': "%(name)s"' % me.__dict__
        if me.flags:
            r+= ', flags %(flags)s' % me.__dict__
        r+= ', size %(width)d' % me.__dict__
        if me.height!=1:
            r+= 'x%(height)d' % me.__dict__
        return r
    def clone( me, prefix ='', suffix ='', kargs_field ={}, **kargs):
        f = me.__class__( **me.__dict__)
        if f.name and me.typ != 'outside':
            f.name = prefix + f.name + suffix
        if kargs_field or kargs:
            f.fielddata = f.fielddata.copy()
            f.fielddata.update( kargs_field)
            f.fielddata.update( kargs)
        return f
    def getType( me):
        return me.subtyp or me.typ

def r_fields():
    r = ''
    r_head = ''
    for k in field_types:
        if r: r += '|'
        #e.g. \\[([^\\[]*\\]
        typ = k[1:-1]
        r += '\\'+k[0]+'(?P<'+typ+'>[^\\'+k[-1]+']*)\\'+k[-1]+'\s*'
        r_head += '\\'+k[0]
    return '(?P<outside>[^\s'+r_head+'][^'+r_head+']+)|' + r
def r_entry():
    r_flags = flags.join_tokens( '')
    r_input_flags = input_types.join_tokens( '')
    return '(?P<flags>['+r_input_flags+r_flags+']*)\s*' + '(?P<name>[\w\.]+)\s*$'


class Panel( object):
    Field = Field
    field_re = re.compile( r_fields() )
    entry_re = re.compile( r_entry() )
    #outside_re = re.compile( '^\s*(?P<name>[\s\S]*)$')
    fielddata = property( lambda me: me.header)

    def __init__( me, txt =None, field_map =(), prefix ='', **kargs_header):
        me.header = kargs_header.copy()
        me.panels = []                #sub-structure skeleton
        me.max_columns = 0
        me.rows = []                  #row = list of Field()s
        me.field_map = {}
        if txt:
            me.add_txt( txt, field_map, prefix=prefix)

    def calc_max_columns( me):
        if me.rows:
            me.max_columns = max( me.max_columns, len( me.rows[-1] ) )

    def add_txt( me, txt, field_map =(), prefix='', **kargs):
        f = me.field_map
        for k in field_map:
            if k in f:
                print """!Warning: %s: field_map[%s]
                        overrides previous definition, maybe duplicated""" % (me,k)
            f[ prefix+k] = field_map[k]
        me.parse( txt, prefix=prefix, **kargs)

    def __iadd__( me, item):            #add item in a new row after last
        if item is None:
            me.rows.append( [] )        #empty row
        else:
            if type(item) is type(''):
                me.parse( item)
            elif type(item) is type( () ):
                txt, field_map = item
                me.add_txt( txt, field_map)
            else:
                if isinstance( item, me.__class__):
                    me.panels.append( item)
                me.rows.append( [ item ] )
        me.calc_max_columns()
        return me
    __add__ = __iadd__                  #left associative : a+b+c does same as a+=b;a+=c

    def __imul__( me, item):            #add item/panel to last row
        if type(item) is type( () ):
            txt, field_map = item
            me.add_txt( txt, field_map, start_new_row=False)
        else:
            if type(item) is type(''):
                print '!Warning: cannot append row inline, wrapping in a panel'
                item = me.__class__( item)
            if isinstance( item, me.__class__):
                me.panels.append( item)
            if not me.rows: me.rows.append( [] )
            me.rows[-1].append( item)
        me.calc_max_columns()
        return me
    __mul__ = __imul__                  #left associative : a*b*c does same as a*=b;a*=c

    header_re = re.compile( '^\s*@'+
                    #'(?P<name>[\w\.]*)' +
                    '\s*(?P<title>[\s\S]*)$'
                )

    def parse( me, txt, prefix ='', start_new_row =True ):    #left to right, top to bottom
        rows = me.rows
        lines = txt.split('\n')
        l=0
        for line in lines:
            l+=1
            row = []
            #print
            line.rstrip()
            if line:
                if l==1:               #first line only
                    hmatch = me.header_re.match( line)
                    if hmatch:
                        me.header.update( hmatch.groupdict() )
                        continue        #consumed
                for fmatch in me.field_re.finditer( line):
                    pos = fmatch.start()
                    #print pos,
                    for typ,entry in fmatch.groupdict().iteritems():
                        if entry is None: continue
                        if not entry:   #column delimiter
                            continue

                        #print typ,':','"'+entry+'";',
                        f = Field( typ= typ, width= 2+len( entry), pos= pos)
                        ematch = None
                        if typ != 'outside':
                            ematch = me.entry_re.match( entry)
                            if ematch is not None:
                                #print ' ', ematch.groupdict()
                                f.__dict__.update( ematch.groupdict() )
                                if f.name and prefix: f.name = prefix + f.name
                                if flags.empty in f.flags:
                                    f.typ = 'empty'
                                if flags.extend in f.flags:
                                    #based on name & pos
                                    for f_above in rows[-1]:
                                        #print 'try..', f_above
                                        if f_above._extender:
                                            f_above = f_above._extender
                                        if f_above.name == f.name and f_above.pos == pos:
                                            f_above.height += 1
                                            f._extender = f_above
                                            break
                            else:
                                f.subtyp = '!Error'
                                print '!Error in panel-parser at line', l, 'pos',pos,': "'+ entry +'"'  # in', line[fmatch.start():fmatch.end()]
                                print line
                                print ' '*pos+'^'
                        fielddata = None
                        if ematch is None:
                            name = entry
                            name = name.strip()
                            if not name:
                                continue
                            f.name = name
                            f.width = len(name)
                        else:
                            if me.field_map:
                                try: fielddata = me.field_map[ f.name]
                                except KeyError: pass
                        f.setup( fielddata)
                        row.append( f)
                        #print f

            if start_new_row or not rows:
                rows.append( row )
            else:
                rows[-1] += row
            me.calc_max_columns()
        if rows:
            if not rows[-1]: del rows[-1]
        #return rows
        #me._print()

    def __str__( me):
        return '%s %s' % ( me.__class__.__name__, me.header)
    def _print( me, pfx ='', mode =None):
        print pfx+str(me), me.max_columns, 'columns'
        for row in me.rows:
            apfx = '+'
            if row:
                for f in row:
                    if isinstance( f, me.__class__):
                        f._print( pfx+'    ', mode=mode)
                    else:
                        if mode != 'panels':
                            if not f or not f._extender:
                                print pfx,apfx, f
                                apfx = ' '
                                if mode == 'map':
                                    print pfx,apfx,'     ', f.fielddata
            else:
                if mode!='panels':
                    print pfx,apfx
        #for p in me.panels:
        #    p._print( pfx+'    ')
        #print pfx+'map', me.field_map

    def clone( me, prefix ='', kargs_field ={}, **kargs_header):
        r = me.__class__()
        r.__dict__ = me.__dict__.copy()
        r.header = me.header.copy()
        r.header.update( kargs_header)
        r.rows = [
                    [ f and f.clone( prefix, kargs_field=kargs_field)  for f in row]
                    for row in me.rows
                 ]

        r.panels = [ f.clone( prefix, kargs_field=kargs_field) for f in me.panels]
        f = {}
        for k,v in me.field_map.iteritems():
            f[ prefix+k] = v
        r.field_map = f
        return r

    def walk( me, visitor):
        a_panel = visitor.openPanel( me)
        for row in me.rows:
            a_row = visitor.openRow( row)
            for f in row:
                if isinstance( f, me.__class__):
                    a_f = visitor.openField( f)
                    f.walk( visitor)
                    visitor.closeField( a_f)
                else:
                    if visitor.config__walk_extender or not f or not f._extender:
                        a_f = visitor.openField( f)
                        visitor.addField( f)
                        visitor.closeField( a_f)
            visitor.closeRow( a_row)
        visitor.closePanel( a_panel)

    class Visitor:
        config__walk_extender = False
        def openPanel ( me, panel):   pass
        def openRow   ( me, row  ):   pass
        def openField ( me, field):   pass
        def addField  ( me, field):   pass
        def closeField( me, field):   pass
        def closeRow  ( me, row  ):   pass
        def closePanel( me, panel):   pass

    class Printer( Visitor):
        def __init__( me, pfx ='    ', mode =None):
            me._pfx = pfx
            me.mode = mode
            me.level = -1
        def openPanel( me, panel):
            me.level += 1
            me.pfx = me._pfx * me.level
            print me.pfx+'Panel', panel.header, panel.max_columns, 'columns'
            return panel
        def openRow( me, row):
            me.apfx = '+'
            return row
        def addField( me, field):
            if me.mode != 'panels':
                print me.pfx, me.apfx, field
            me.apfx = ' '
        def closeRow( me, row):
            if me.mode != 'panels':
                if me.apfx == '+' and not row:    #empty - row with extenders is not considered empty
                    print me.pfx, me.apfx
        def closePanel( me, panel):
            me.level -= 1
            me.pfx = me._pfx * me.level

    class Checker( Visitor):
        def __init__( me, message ='Warning'):
            me.message = message
        def openPanel( me, panel):
            me.panel = panel
            me.field_map = panel.field_map and panel.field_map.copy() or {}
        def addField( me, field):
            if field:
                try:
                    del me.field_map[ field.name ]
                except KeyError: pass
        def closePanel( me, panel):
            if me.field_map:
                print '!%s: %s: unused fields in .field_map:\n  %s' % (me.message, me.panel, ', '.join( me.field_map.iterkeys() ) )

    def check( me, **k):
        me.walk( me.Checker( **k))

if __name__ == '__main__':

    a = """
     [_ log.enabled]   [? dir.change_root]      other one     []  bozoa [@pipo]
    [   log.name]      [  log.size]             {  dir.change_response.label}
    [+  log.name]      < trace.show>            [? dir.change_response]
    [+  log.name]                               [+  dir.change_response]
      some text        < log.show>              [+  dir.change_response]
    """



    panel_log_trace= Panel( """\
        @Logging control
    [_ log.enabled]     < log.view   >      logging to:[ log.name ]
    [_ trace.enabled]   < trace.view >      logging to:[ trace.name ]
    < trace.clear >
    """)

    panel_sniff= Panel( """\
        @Sniffing
    [_ sniff.enabled]
    """) + panel_log_trace.clone( 'sniff.')


    panel_term = (
    Panel("""\
        @Terminal Console
    [? term.name]               [? term.work_mode]
    [? term.root_dir]
    """)
    +Panel( "@messaging" )
     *panel_log_trace
    +panel_sniff
    +("""\
        @Status line

    {term.connected}   {term.root_dir}   {response.dir}   {trace.dir}
    {+ term.connected}
    """)
    )

    from util.mix import Grab_stdout
    from util.diff import diff
    import unittest
    class t_Panel( unittest.TestCase):
        def test0_panel_ops( me):
            pa = Panel(a)
            pa += None
            pa *= None
            pa *= 'boza',{}

            s = Grab_stdout()
            pa._print()
            expect = """\
Panel {} 5 columns
 +
 +   5: input-Checkbox: "log.enabled", size 15
    23: input-Chooser: "dir.change_root", size 19
    48: outside: "other one", size 9
    66: outside: "bozoa", size 5
    72: empty: "pipo", flags @, size 7
 +   4: input-Text: "log.name", size 13x3
    23: input-Text: "log.size", size 12
    48: label: "dir.change_response.label", size 29
 +  23: button: "trace.show", size 13
    48: input-Chooser: "dir.change_response", size 23x3
 +   6: outside: "some text", size 9
    23: button: "log.show", size 11
 + None
     0: outside: "boza", size 4
"""
            s.release()
            result = str(s)
            #print result
            if result != expect:
                print result
                df = '\n'.join( diff( result, expect, 'result', 'expect') )
                me.failUnless( result == expect, 'result != expect\n'+df)


        def compare( me, mode='panelsz'):
            s = Grab_stdout()
            panel_term._print( mode=mode)
            p = str(s)
            s.release()
            s.grab()
            panel_term.walk( Panel.Printer( mode=mode ))
            q = str(s)
            s.release()
            if p != q:
                print q
                df = '\n'.join( diff( p,q, '_print recursive', 'Printer visitor'))
                me.failUnless( p == q, '_print != visitor\n'+df)

        def test_compare_print_visitor_panels( me):
            me.compare( mode='panels')
        def test_compare_print_visitor_panels( me):
            me.compare( mode='nopanelsz')

    if 0:
        p = Panel( panel_term)
        panel_sniff._print()

    unittest.main()

# vim:ts=4:sw=4:expandtab
