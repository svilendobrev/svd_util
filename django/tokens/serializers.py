from django.utils.translation import ugettext as _
from rest_framework import serializers

from .utils import decode_oid


class OidAndTokenSerializer(serializers.Serializer):
    '''
    Fix exception handling, handle binascii.Error and don't crash

    '''
    oid = serializers.CharField()
    token = serializers.CharField()

    default_error_messages = {
        'invalid_oid': _('Invalid id'),
        'invalid_token': _('Invalid token'),
    }

    def get_object(self, pk):
        raise NotImplementedError

    def validate_oid(self, value):
        err = serializers.ValidationError(self.error_messages['invalid_oid'])
        try:
            oid = decode_oid(value)
        except (ValueError, TypeError, OverflowError):
            raise err

        if not oid.isdigit():
            raise err

        self.obj = self.get_object(pk=oid)
        if not self.obj:
            raise err
        return value

    def validate(self, attrs):
        attrs = super(OidAndTokenSerializer, self).validate(attrs)
        if not self.context['view'].token_generator.check_token(attrs['token'], self.obj):
            raise serializers.ValidationError(self.error_messages['invalid_token'])
        return attrs
