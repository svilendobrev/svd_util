#s.dobrev 2k3-4
from __future__ import print_function #,unicode_literals

from svd_util.ui.layout import Panel
from . import html

class BuilderHTML( Panel.Visitor):
    config__walk_extender = False
    config__no_factories = False

    config__title_table = False
    panel = None
    title = ''  #root

    def __init__( me, fieldDataGetter =None, panel =None, config__title_table =None):
        me.fieldDataGetter = fieldDataGetter
        me.out = ''
        me.level = []
        me._levels = 0
        me.table = None
        me.focusmap = {}
        if config__title_table is not None: me.config__title_table = config__title_table
        panel = panel or me.panel
        if panel: panel.walk( me)

    def map( me, fieldname, docAddress):
        me.focusmap[ fieldname] = docAddress
    def __iadd__( me, a):
        me.out += a
        return me

    def openPanel( me, panel):
        title = panel.header.get( 'title', '')
        if not me.level:    #root
            me.title = title or me.title    #paneldef overrides class
        PFX = '    '
        pfx = PFX * me._levels
        me.level.append( me.table)
        me._levels +=1
        me.table = html.TableHTML( out= me, pfx= pfx)
        if title:
            title_table = panel.header.get( 'title_table', me.config__title_table)
            if title_table:
                try: 'a' in title_table
                except TypeError: title_table = '-'

                h = panel.header.get( 'header4title', { 'width':'100%'} )
                style = h.get( 'style', 'H4')
                me.table.head( max_columns=2, **h)      #hackish!
                txt_now = pfx+' <tr>\n'
                txt_after = ''

                ttl = ' <%s> %s </%s>\n' % (style, html.htmlize_br( title), style)
                td_title = ''
                td_table = ''

                align = ''
                if 'right'    in title_table: align = 'align=right'
                elif 'center' in title_table: align = 'align=center'

                if 'nooutdent' in title_table or 'center' in title_table:
                    ttl_colspan = ''
                    ttl_column  = ''
                else:
                    ttl_colspan = 'colspan=2'
                    ttl_column  = '  <td width=20>\n'     #empty column

                if 'above' in title_table:
                    txt_now  += pfx+'  <td %(ttl_colspan)s %(align)s>' % locals() + ttl
                    txt_now  += pfx+' <tr>\n'
                    td_title += pfx+ttl_column
                elif 'below' in title_table:
                    td_title += pfx+ttl_column
                    txt_after+= pfx+' <tr>\n'
                    txt_after+= pfx+'  <td %(ttl_colspan)s %(align)s>' % locals() + ttl
                else:
                    td_title += pfx+'  <td width=70>' + ttl     #middle

                td_table += pfx+'  <td>\n'

                if 'right' in title_table:
                    txt_now += td_table
                    txt_after = td_title + txt_after
                else:
                    txt_now += td_title + td_table
                txt_after += pfx+'</table>\n'      # +'<hr>\n'

                me.out += txt_now
                me.table._after = txt_after
                me.table.pfx += PFX
                me._levels +=1


        me.table.config__no_factories = me.config__no_factories
        me.table.panel = panel
        me.table.head( max_columns= panel.max_columns, **panel.header )    #layout =column sizes
        return me.table

    def openRow( me, row, align= 'left'):
        me.table.row_head( row, align=align)

    _cell_defaults = { 'align':   'left',
                       'valign':  'top',
                       'colspan': 1,
                    }
    def openField( me, field):
        fd = getattr( field, 'fielddata', None)
        if fd:
            d = me._cell_defaults.copy()
            d.update( fd)
        else: d = me._cell_defaults
        me.table.cell_head( **d)

    def addField( me, field):
        if field and field.typ != 'empty':
            fd = field.getFieldData()
            if me.fieldDataGetter and field.typ != 'outside':
                me.fieldDataGetter( fd.name, fd, do_err= False)
        else: fd = None
        me.table.cell_body( fd )
    def closeRow( me, row): pass
    def closePanel( me, panel):
        me.table.tail()
        _after = getattr( me.table, '_after', None)
        if _after is not None:
            me.out += _after
            me._levels -=1
        me.table = me.level.pop()
        me._levels -=1

    def __str__( me): return me.out

# vim:ts=4:sw=4:expandtab
