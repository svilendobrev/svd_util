import itertools

def collect( name, viewset_bases, localattrs ={}):
    items = tuple( filter( bool, (getattr( b, name, None) for b in viewset_bases)))
    local = localattrs.get( name)
    if local: items = (local,) + items
    return items

#HACKfix XXX - works only for serlzs declared after this  (also see below alternative ..)
from rest_framework.serializers import SerializerMetaclass
_get_declared_fields = SerializerMetaclass._get_declared_fields
SerializerMetaclass._get_declared_fields = lambda bases, attrs: _get_declared_fields( tuple(reversed(bases)), attrs)

def make_serializer( name, viewset_bases, parent_name =None):
    bases = collect( name, viewset_bases)
    if not bases: return None
    #print( '+glue', parent_name, name, bases)
    if parent_name: name += '4'+parent_name

    #accumulate Meta.* into one
    attrs = {}
    metas = [ b.Meta for b in reversed( bases) if hasattr( b, 'Meta') ] #start with most base
    if metas:
        meta = {}
        for m in metas:
            for k in dir( m):
                if k.startswith('__'): continue
                v = getattr( m,k)
                if isinstance( v, (list,tuple)):
                    meta.setdefault( k, []).extend( v)
                elif isinstance( v, dict):
                    meta.setdefault( k, {}).update( v)
                else:
                    assert k not in meta, (k, v, meta[k])
                    meta[k] = v

        attrs['Meta'] = type( 'gluedMeta_'+name, (), meta)

    #XXX bases = tuple( reversed(bases))     # alternative XXX HACKfix for SerializerMetaclass._get_declared_fields .. only for gluedSerializers
    r = type( 'glued_' +name, bases, attrs)
    o = r._declared_fields.__class__( sorted( r._declared_fields.items()) )
    for k in [ 'url', 'id', ]: #this order - last goes first
        if k in o:
            o.move_to_end( k, last=False)
    r._declared_fields = o
    return r

def make_permissions( name, viewset_bases, parent_name =None):
    bases = collect( name, viewset_bases)
    return tuple( itertools.chain.from_iterable( bases))


class glue4viewsets( type):
    'metaclass for gluing many mixins with their serializer_classes/permission_classes'

    pre_bases = ()
    gluers = dict(  #name = gluer   ; def gluer( name, bases)
        serializer_class = make_serializer,
        permission_classes = make_permissions,
    )
    def __new__( klas, name, bases, attrs):
        gluers = dict( (k, gluer( k,bases,name)) for k,gluer in klas.gluers.items())
        overlaps = set(attrs) & set(gluers)
        assert not overlaps, ('do not inject gluers in result class - use a mixin', overlaps)
        attrs.update( gluers)
        return super().__new__( klas, name, klas.pre_bases + bases, attrs)

# vim:ts=4:sw=4:expandtab
