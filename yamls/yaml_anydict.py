
import yaml
from yaml.representer import Representer
from yaml.constructor import Constructor, MappingNode, ConstructorError


def dump_anydict_as_map( anydict):
    yaml.add_representer( anydict, _represent_dictorder)
def dump_anydict_as_map_inheriting( anydict):
    yaml.add_multi_representer( anydict, _represent_dictorder)
def _represent_dictorder( self, data):
    return self.represent_mapping( 'tag:yaml.org,2002:map', data.items() )

# for v3.12 from 8.2016 adds explicit OrderedDict...
# so Do this before any inheritance of Representer XXX like Dumper
import collections
#yaml.representer.Representer.yaml_representers.pop( collections.OrderedDict, None)
yaml.representer.Representer.yaml_representers[ collections.OrderedDict] = _represent_dictorder

def dump_seq_as_list( seq, Base= Representer):
    yaml.add_representer( seq, Base.represent_list)
def dump_tuple_as_list(): dump_seq_as_list( tuple)

def load_list_as_tuple():
    'and so is hashable'
    yaml.add_constructor( 'tag:yaml.org,2002:seq', Constructor.construct_python_tuple)


class Loader_map_as_anydict( object):
    'inherit + Loader'
    anydict = None      #override
    @classmethod        #and call this
    def load_map_as_anydict( klas):
        yaml.add_constructor( 'tag:yaml.org,2002:map', klas.construct_yaml_map)

    'copied from constructor.BaseConstructor, replacing {} with self.anydict()'
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_mark)
        mapping = self.anydict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError as exc:
                raise ConstructorError("while constructing a mapping", node.start_mark,
                        "found unacceptable key (%s)" % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    def construct_yaml_map( self, node):
        data = self.anydict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

# vim:ts=4:sw=4:expandtab
