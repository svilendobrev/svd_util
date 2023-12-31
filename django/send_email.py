import os
import collections
import mimetypes
from email.mime.image import MIMEImage
from django.conf import settings
from django.db.models import Q
from django.template import loader
from django.core.mail import EmailMultiAlternatives as _EmailMultiAlternatives, EmailMessage as _EmailMessage, get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.contrib.auth import get_user_model

import logging
logger = logging.getLogger(__name__)


class LogMessageMixin:
    def send(self, *a, **ka):
        logger.info('Sending email message to %s', self.recipients())
        return super().send( *a, **ka)

class EmailMessage( LogMessageMixin, _EmailMessage): pass
class EmailMultiAlternatives( LogMessageMixin, _EmailMultiAlternatives): pass

def make_email_message(to_email, from_email, context, subject_template_name,
               plain_body_template_name=None,
               html_body_template_name=None, html_body_template_images=(),
               cc=None, bcc=None
               ):
    assert plain_body_template_name or html_body_template_name
    assert to_email or cc or bcc

    if not plain_body_template_name:
        if settings.EMAIL_USE_NOHTML and html_body_template_name:
            plain_body_template_name = html_body_template_name

    if settings.EMAIL_USE_NOHTML:
        html_body_template_name = None
        html_body_template_images = ()

    if to_email and not isinstance(to_email, (list, tuple)):
        to_email = [to_email]

    context = context or {}
    context.setdefault('EMAIL_SUBJECT_PREFIX', getattr(settings, 'EMAIL_SUBJECT_PREFIX', ''))

    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())

    msg_kwargs = dict(cc=cc, bcc=bcc)
    if plain_body_template_name:
        plain_body = loader.render_to_string(plain_body_template_name, context)
        msg = EmailMultiAlternatives(subject, plain_body, from_email, to_email, **msg_kwargs)
        if html_body_template_name:
            html_body = loader.render_to_string(html_body_template_name, context)
            msg.attach_alternative(html_body, 'text/html')
    else:
        html_body = loader.render_to_string(html_body_template_name, context)
        msg = EmailMessage(subject, html_body, from_email, to_email, **msg_kwargs)
        msg.content_subtype = 'html'

    if html_body_template_name and html_body_template_images:
        msg.mixed_subtype = 'related'
        for fpath in html_body_template_images:
            mime = mimetypes.guess_type( fpath)[0]
            subtype = None
            if mime and '/' in mime:
                _zz, subtype = mime.split('/')
            filename = os.path.basename( fpath)
            try:
                fimg = open( fpath, 'rb')
            except FileNotFoundError:
                import traceback
                traceback.print_exc()
            else:
                with fimg as f:
                    content = f.read()
                    img = MIMEImage( content, subtype)
                    img.add_header('Content-Disposition', 'inline', filename=filename)
                    img.add_header('Content-ID', f'<{filename}>')
                    msg.attach( img)
    return msg


def send_email(*args, **kwargs):
    msg = make_email_message(*args, **kwargs)
    msg.send()


default_config = dict(
    WHITELIST = None,       # list of email addresses, case insensitive
    STAFF_ONLY = None,      # bool, set to True to require user.is_staff=True
    JOINED_BEFORE = None,   # date users signed up before
    JOINED_AFTER = None,    # date users signed up after
    UNKNOWN_USER = None,    # bool, set to True if sending mails to unknown addresses is needed

    LOGIC = 'and',          # "and" - all filters need to be satisfied; "or" - at least one filter to be satisfied
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend',
)

def get_config():
    config = getattr(settings, 'EMAIL_FILTER_RECIPIENTS', {}).copy()
    for k,v in default_config.items():
        if k not in config:
            config[k] = v
    assert set(default_config) == set(config), 'Unknown keys in EMAIL_FILTER_RECIPIENTS setting: %s' % list((set(config) - set(default_config)))
    return config


class FilterEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently)
        self.init_kwargs = kwargs

    def send_messages(self, email_messages, **kwargs):
        logger.debug('Sending %d email message(s)', len(email_messages))
        config = get_config()
        msg2blocked = collections.defaultdict( dict)  # { msg: { filter_name: list_of_blocked_recipients }}
        filters = set()
        for name, value in config.items():
            if value is None:
                continue
            meth = getattr(self, '_email_%s' % name.lower(), None)
            if not meth:
                continue
            filters.add( name)
            for msg, blocked in meth( email_messages, value).items():
                if blocked:
                    msg2blocked[ msg][ name] = blocked

        messages = email_messages  # default if no filters configured
        if filters:
            logic = config['LOGIC'].lower()
            if logic == 'and':
                messages = [m for m in email_messages if m not in msg2blocked]
            elif logic == 'or':
                messages = [m for m in email_messages if set(msg2blocked[ m]) != filters]  # not blocked by all filters
            else:
                assert 0, 'unknown LOGIC value in EMAIL_FILTER_RECIPIENTS setting: %s' % logic

        # only for logging
        if len(messages) != len(email_messages):
            recp2filters = {}
            for m, blocked in msg2blocked.items():
                for name, recps in blocked.items():
                    for recp in recps:
                        recp2filters.setdefault( recp, set()).add( name)
            s = []
            for recp, filters in sorted(recp2filters.items()):
                s.append( '%s was blocked by %s' % (recp, [ f'EMAIL_FILTER_{fname.upper()}' for fname in sorted( filters)]) )
            logger.warning('Email recipients blocked by filters: %s', '; '.join( s))

        if messages:
            conn = get_connection( backend=config['EMAIL_BACKEND'], **self.init_kwargs)
            return conn.send_messages( messages, **kwargs)
        return 0  # number of messages sent

    def _email_whitelist(self, email_messages, whitelist):
        whitelist = set(s.lower().strip() for s in whitelist)
        return self._filter( email_messages, lambda recp: recp in whitelist)

    def _email_staff_only(self, email_messages, staff_only):
        chk = None if not staff_only else self._user_check( Q(is_staff=True))
        return self._filter( email_messages, chk)

    def _email_joined_before(self, email_messages, date):
        return self._filter( email_messages, self._user_check( Q(created__date__lt=date)))

    def _email_joined_after(self, email_messages, date):
        return self._filter( email_messages, self._user_check( Q(created__date__gte=date)))

    def _email_unknown_user(self, email_messages, unknown_user):
        chk = None if unknown_user else self._user_check( Q())
        return self._filter( email_messages, chk)

    def _filter(self, email_messages, check=None):
        if not check:
            return dict.fromkeys( email_messages, {})
        res = {}
        for msg in email_messages:
            blocked_recp = set()
            for recp in set(s.lower().strip() for s in msg.recipients()):
                if not check( recp):
                    blocked_recp.add( recp)
            res[ msg] = blocked_recp
        return res

    def _user_check( self, q):
        return lambda recp: get_user_model().objects.filter( q, is_active= True, email__iexact= recp).exists()


# don't silently pass refusal from postmark about zero-sized attachments
try:
    from anymail.backends.postmark import EmailBackend as PostmarkBackend
except ImportError:
    pass
else:
    from anymail.exceptions import AnymailRequestsAPIError

    class FixedPostmarkBackend(PostmarkBackend):
        zero_sized_attachment_error = {'ErrorCode': 300, 'Message': 'Zero-sized attachments not allowed.'}
        def parse_recipient_status(self, response, payload, message):
            parsed_response = self.deserialize_json_response(response, payload, message)
            if parsed_response == self.zero_sized_attachment_error:
                raise AnymailRequestsAPIError('Zero-sized attachments not allowed.',
                    email_message=message, payload=payload, response=response,
                    backend=self)
            return super().parse_recipient_status( response, payload, message)


# vim:ts=4:sw=4:expandtab
