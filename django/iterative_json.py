import sys
import six
import ijson
from django.core.serializers.json import Serializer as _Serializer, PythonDeserializer, DeserializationError


'''
This makes it possible to run django loaddata command with large files and consume less memory.

In your settings.py add:
SERIALIZATION_MODULES = dict(json='svd_util.django.iterative_json')

'''


Serializer = _Serializer


def Deserializer(stream_or_string, **options):

    if isinstance(stream_or_string, six.string_types):
        stream_or_string = six.BytesIO(stream_or_string.encode('utf-8'))
    try:
        objects = ijson.items(stream_or_string, 'item')
        for obj in PythonDeserializer(objects, **options):
            yield obj
    except GeneratorExit:
        raise
    except Exception as e:
        # Map to deserializer error
        six.reraise(DeserializationError, DeserializationError(e), sys.exc_info()[2])

# vim:ts=4:sw=4:expandtab
