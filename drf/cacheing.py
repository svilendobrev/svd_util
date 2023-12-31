from rest_framework import serializers

#serializers.fields are always same but are re-invented over and over.. cache them:
# gives 20% faster loading..
# XXX but if whole serializer-instances are cached, it is 25% and this is redundant

class myMeta4Cache_fields_Srlz( serializers.SerializerMetaclass):
    def __init__( me, name, bases, dct):
        super().__init__( name, bases, dct)
        if 'Meta' in dct and hasattr( me.Meta, 'model'):
            me._fields_ = me().get_fields()

class Cache_fields_Srlz( serializers.Serializer, metaclass = myMeta4Cache_fields_Srlz):
    'beware: only one active instance per serklas allowed (dead/used-out are okay)'
    @property
    def fields(self):
        if not hasattr(self, '_fields'):
            self._fields = serializers.BindingDict(self)
            for key, value in self._fields_.items():
                self._fields[key] = value
        return self._fields

#TODO: metaclass-level cache for whole-serializers-instances=singletons

############

class PrimaryKeyRelatedField_cached( serializers.PrimaryKeyRelatedField):
    '''data-level snapshot cache: 50% faster loading when nomenclatures cached this way
    use it transaction-like, wrapping actions which need consistent snapshot
    '''
    _cache_klas2values = {}
    def to_internal_value(self, data):
        rel_to = self.queryset.model #rel.to
        if rel_to in self._cache_klas2values:
            return self._cache_klas2values[ rel_to].get( data)
        return super().to_internal_value( data)

    @classmethod
    def load_cache( klas, models, pk =None):
        for model in models:
            klas._cache_klas2values[ model] = dict( (getattr( i, pk or 'pk'),i) for i in model.objects.all())
    @classmethod
    def stop_cache( klas):
        klas._cache_klas2values.clear()

__all__ = '''
Cache_fields_Srlz
PrimaryKeyRelatedField_cached
'''.split()

# vim:ts=4:sw=4:expandtab
