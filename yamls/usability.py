# sdobrev 2011
'usability-tuned yaml i/o - human re-editable - aligned, ordered, min-clutter'

from collections import OrderedDict

import yaml
from . import yaml_anydict, yaml_extra

class Dumper( yaml_extra.Dumper_AlignMapValues,
              yaml_extra.Dumper_PreferBlock_for_Multiline,
              yaml_extra.Dumper_AllowExtraWidth_for_Singleline,
            yaml.Dumper ):
    extra_width = 15

    def represent_list( self, data):
        #if len( data) == 0: return
        if len( data) == 1:
            return self.represent_data( tuple(data)[0] )
        return super( Dumper, self).represent_list( data)


class Loader( yaml_anydict.Loader_map_as_anydict, yaml.Loader):
    anydict = OrderedDict

def dump( d, **kargs):
    return yaml.dump( d, allow_unicode= True, default_flow_style= False, Dumper= Dumper, **kargs)
        #width=90,

def load( f, retab =4, **kargs):
    if retab:
        if not isinstance( f, str):
            f = f.read()
        f = f.expandtabs( retab)
    return yaml.load( f, Loader= Loader, **kargs)

#yaml_anydict.dump_anydict_as_map_inheriting( OrderedDict)
yaml_anydict.dump_anydict_as_map_inheriting( dict)
yaml_anydict.dump_seq_as_list( tuple, Base=Dumper)
yaml_anydict.dump_seq_as_list( set,   Base=Dumper)
yaml_anydict.dump_seq_as_list( list,  Base=Dumper)

Loader.load_map_as_anydict()
yaml_anydict.load_list_as_tuple()

if __name__ == '__main__':
    import sys
    d = load( open( sys.argv[1]) )
    print( dump( d ))

# vim:ts=4:sw=4:expandtab
