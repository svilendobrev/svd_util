from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


def encode_oid(pk):
    return urlsafe_base64_encode(force_bytes(pk)).decode()


def decode_oid(pk):
    return force_text(urlsafe_base64_decode(pk))

