import datetime

from django.utils import six
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
from django.utils import timezone


class TokenGenerator(object):
    '''
    A more generic version of django.contrib.auth.tokens.PasswordResetTokenGenerator.
    Every two-step-confirmed-by-token api operation should have its own token generator
    that deals with token expiration and ensures a token can only be used once.
    '''

    TOKEN_LIFETIME_HOURS = None
    key_salt = "lib.tokens.TokenGenerator"

    def check_token(self, token, *args):
        # Parse the token
        try:
            ts_b36, hash = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(ts, *args), token):
            return False

        # Check the timestamp is within limit
        lifetime_hours = self.get_token_lifetime_hours()
        if lifetime_hours is not None:
            if (self._hours(timezone.now()) - ts) > lifetime_hours:
                return False
        return True

    def get_token_lifetime_hours(self):
        return self.TOKEN_LIFETIME_HOURS

    def make_token(self, *args):
        ts = self._hours(timezone.now())
        return self._make_token_with_timestamp(ts, *args)

    def _make_token_with_timestamp(self, timestamp, *args):
        # timestamp is number of hours since 2001-1-1.  Converted to
        # base 36, this gives us a string of digits
        ts_b36 = int_to_base36(timestamp)

        # By hashing on the internal state of the args and using state
        # that is sure to change (e.g. the password salt will change as soon as
        # the password is set, at least for current Django auth, and
        # last_login will also change), we produce a hash that will be
        # invalid as soon as it is used.
        # We limit the hash to 20 chars to keep URL short

        hash = salted_hmac(
            self.key_salt,
            self._make_hash_value(timestamp, *args),
        ).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)

    def _make_hash_value(self, timestamp, *args):
        return six.text_type(timestamp)

    def _hours(self, now):
        seconds = round(
            (now - timezone.make_aware(datetime.datetime(2001, 1, 1))).total_seconds()
        )
        return seconds // 3600  # hours
