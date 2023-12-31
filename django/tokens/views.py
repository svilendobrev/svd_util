from django.conf import settings
from svd_util.django.send_email import send_email
from .utils import encode_oid


class ConfirmationEmailViewMixin(object):
    token_generator = None
    subject_template_name = None
    plain_body_template_name = None
    html_body_template_name = None

    def send_email(self, to_email, from_email, context):
        send_email(to_email, from_email, context, **self.get_send_email_extras())

    def get_send_email_kwargs(self, to_email, *args):
        return {
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'to_email': to_email,
            'context': self.get_email_context(*args),
        }

    def get_send_email_extras(self):
        return {
            'subject_template_name': self.subject_template_name,
            'plain_body_template_name': self.plain_body_template_name,
            'html_body_template_name': self.html_body_template_name,
        }

    def get_email_context(self, user):
        token = self.token_generator.make_token(user)
        oid = encode_oid(user.pk)
        return {
            'user': user,
            'oid': oid,
            'token': token,
        }
