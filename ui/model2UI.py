'apply klas.UI_metadata to relevant panel-tree'

import layout

class Visitor( layout.Panel.Visitor):
    '''for statictyped attributes of klas if they have UI_metadata,
        update the panels at ANY level
    '''
    #TODO look through structures
    #TODO Panel's fieldmap to autocontain all fields (with empty value if need be)
    names = 'label width'.split()
    def __init__( me, klas): me.klas = klas
    def openPanel( me, panel):
        #print panel.header.get('title', 'nema')
        fmap = panel.field_map
        for k,typ in me.klas.StaticType.iteritems():
            for name in me.names:
                value = typ.UI[ name ] #= typ.UI_label / getattr ??
                if not value: continue
                props = fmap.setdefault( k, {})
                props.setdefault( name, value)

def model2UI( layout, klas):
    layout.walk( Visitor( klas) )
    return layout

# vim:ts=4:sw=4:expandtab
