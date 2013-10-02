#import yaml

##vim error: autocmd FileType yaml setl errorformat=%Ayaml%.%#,%Z\ %#in\ \"%f\"\\,\ line\ %l\\,\ column\ %c,%C%m

from yaml.nodes import ScalarNode, MappingNode

class Dumper_AlignMapValues( object):
    '''inherit + Dumper ; result like
    one:    1
    two:    2
    three:  3
    four:   4
    eleven: 11
    '''

    #Representer.represent_mapping
    def represent_mapping( self, tag, mapping, flow_style=None):
        node = super( Dumper_AlignMapValues, self).represent_mapping( tag, mapping, flow_style)
        node._keywidth = 0
        if mapping:
            keys = [ k for k,v in node.value]
            simplekeys = sum( isinstance( k,ScalarNode) for k in keys) == len( node.value)
            if simplekeys:
                node._keywidth = max( len( str(k.value)) for k in keys)
        return node

    #Serializer.serialize_node
    def serialize_node( self, node, parent, index):
        if (node not in self.serialized_nodes
            and isinstance( parent, MappingNode)
            and isinstance( node, ScalarNode)
            ):
                if index is None:   # node is a key
                    pass
                else:               # node is a value, index is its key
                    if getattr( parent, '_keywidth', None):  #mapping with _keywidth
                        node.style = ( parent._keywidth - len( index.value ), node.style)
        return super( Dumper_AlignMapValues, self).serialize_node( node, parent, index)

    #Emitter.choose_scalar_style
    def choose_scalar_style( self):
        alignindent = None
        if isinstance( self.event.style, tuple):
            alignindent, self.event.style = self.event.style
        r = super( Dumper_AlignMapValues, self).choose_scalar_style()
        if alignindent is not None and r in ['', "'", '"']:
            data = ' '*alignindent
            self.column += len(data)
            if self.encoding:
                data = data.encode(self.encoding)
            self.stream.write(data)
        return r

###########

class Dumper_PreferBlock_for_Multiline( object):
    '''make default multiline format a block instead of singlequote
    yaml.dump( { 'a':'b\nc', 'x':2 })
    a: |-
      b
      c
    x: 2
    '''
    force_block = False #'|' or '>' : for anything that needs quotes, or longer than 1 line, or mutiline
    shorten_width = 0

    #Emitter
    def analyze_scalar( self, scalar):
        r = super( Dumper_PreferBlock_for_Multiline, self).analyze_scalar( scalar)
        if r.multiline or self.force_block:
            r.lines = [len(l) for l in scalar.splitlines()]
        return r
    #Emitter
    def choose_scalar_style( self):
        r = super( Dumper_PreferBlock_for_Multiline, self).choose_scalar_style()
        if not self.event.style:
            if self.force_block:
                lmax = self.analysis.lines and max( self.analysis.lines) or 0
                if r in ( "'", '"' ) or lmax > self.best_width - self.shorten_width :
                    return self.force_block
                    return lmax > self.best_width - self.shorten_width and '>' or '|'

            if self.analysis.multiline and r in ( "'", '"' ):
                #it autoguessed ' for multiline
                if (not self.flow_level and not self.simple_key_context
                        and self.analysis.allow_block):     #the original condition for |>
                    lmax = max( self.analysis.lines)
                    prefer_style = lmax > self.best_width and '>' or '|'
                    return prefer_style
        return r



class Dumper_AllowExtraWidth_for_Singleline( object):
    'allow singlelines to protrude extra_width more than width'
    extra_width = 10

    #Emitter
    def process_scalar( self):
        if self.analysis is None:
            self.analysis = self.analyze_scalar( self.event.value)
        if self.style is None:
            self.style = self.choose_scalar_style()

        wider = 0
        if (self.style != '"'
                and not self.analysis.multiline
                and self.best_width < len( self.event.value) < self.best_width + self.extra_width
            ):
            wider = self.extra_width
            self.best_width += wider

        r = super( Dumper_AllowExtraWidth_for_Singleline, self).process_scalar()
        self.best_width -= wider
        return r

if __name__ == '__main__':
    import yaml
    def dump( d, Dumper= None, **k):
        class Dumper1( Dumper, yaml.Dumper): pass
        print( '--- # original')
        print( yaml.dump( d, default_flow_style= False, **k))
        print( '--- # ', Dumper.__name__)
        print( yaml.dump( d, default_flow_style= False, Dumper=Dumper1, **k))

    dump( dict(
        one= 1,
        two= 2,
        three= 3,
        four= 4,
        eleven= 11,
        ), Dumper= Dumper_AlignMapValues)

    dump( dict(
        x= 'better\ntext',
        y= 2,
        z= 'oline'
        ), Dumper= Dumper_PreferBlock_for_Multiline )

    dump( dict(
        x= '12 4 '*9,
        y= '123 56 '*8
        ), Dumper= Dumper_AllowExtraWidth_for_Singleline, width=40 )

# vim:ts=4:sw=4:expandtab
