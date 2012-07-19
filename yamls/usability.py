# sdobrev 2011
'usability-tuned yaml i/o - human re-editable - aligned, ordered, min-clutter'

from svd_util.py3 import dictOrder

import yaml
import yaml_anydict, yaml_extra

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
    anydict = dictOrder

def dump( d):
    return yaml.dump( d, allow_unicode= True, default_flow_style= False, Dumper= Dumper)
        #width=90,

#yaml_anydict.dump_anydict_as_map_inheriting( dictOrder)
yaml_anydict.dump_anydict_as_map_inheriting( dict)
yaml_anydict.dump_seq_as_list( tuple, Base=Dumper)
yaml_anydict.dump_seq_as_list( set,   Base=Dumper)
yaml_anydict.dump_seq_as_list( list,  Base=Dumper)

Loader.load_map_as_anydict()
yaml_anydict.load_list_as_tuple()

if __name__ == '__main__':
    import sys
    d = yaml.load( open( sys.argv[1]), Loader= Loader)
    dump( d )

# vim:ts=4:sw=4:expandtab
