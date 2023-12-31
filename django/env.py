from urllib.parse import ParseResult
import environ  # requires django-environ

_ENV = dict(
    from_file = set(),
    used = set(),
)

anymail_backends = dict(
    (f'anymail{name}', f'anymail.backends.{name}.EmailBackend')
    for name in '''
        amazon_ses
        console
        mailgun
        postmark
        mailjet
        mandrill
        sendgrid
        sendinblue
        sparkpost
    '''.split()
)
# fixed error handling in case of zero-sized attachments
anymail_backends['anymailpostmark'] = 'svd_util.django.send_email.FixedPostmarkBackend'

supported_email_schemes = dict(environ.Env.EMAIL_SCHEMES,
    **anymail_backends
)
email_scheme_modifiers = ['rq', 'filter', 'nohtml']
#for pref in email_scheme_modifiers:
#    supported_email_schemes = dict(
#        supported_email_schemes,
#        **dict((k, v) for k,v in supported_email_schemes.items())
#    )

class Env(environ.Env):
    EMAIL_SCHEMES = supported_email_schemes

    @classmethod
    def email_url_config(cls, url, backend=None):
        extra = {}
        scheme = url.scheme
        for pref in email_scheme_modifiers:
            pp = pref + '+'
            extra[ f'USE_{pref}'.upper()] = pp in scheme
            scheme = scheme.replace( pp, '')
        attrs = ('netloc', 'path', 'params', 'query', 'fragment',)
        url = ParseResult(scheme=scheme, **dict( (k, getattr(url, k)) for k in attrs))
        return dict(
            super().email_url_config(url, backend=backend),
            **extra
        )

    def date(self, var, default=environ.Env.NOTSET):
        from django.utils.dateparse import parse_date
        return self.get_value( var, cast=parse_date, default=default)

    def get_value(self, var, *args, **kwargs):
        _ENV['used'].add(var)
        return super().get_value(var, *args, **kwargs)

    @classmethod
    def read_env(cls, env_file=None, **overrides):
        before = set(cls.ENVIRON)
        super().read_env(env_file=env_file, **overrides)
        after = set(cls.ENVIRON)
        _ENV['from_file'] = after - before


def config_email( env):
    res = {}
    config = env.email('EMAIL_URL')
    attrs = '''
        EMAIL_HOST
        EMAIL_PORT
        EMAIL_HOST_USER
        EMAIL_HOST_PASSWORD
        EMAIL_BACKEND
        '''.split()
    for attr in attrs:
        res[ attr] = config[ attr]

    res['EMAIL_USE_TLS'] = config.get('EMAIL_USE_TLS', False)
    res['EMAIL_USE_SSL'] = config.get('EMAIL_USE_SSL', False)
    res['DEFAULT_FROM_EMAIL'] = res['EMAIL_HOST_USER']

    anymail_settings = res['ANYMAIL'] = {}
    if res['EMAIL_BACKEND'] in anymail_backends.values():
        service_provider = dict( (v,k) for k,v in anymail_backends.items())[ res['EMAIL_BACKEND'] ]
        assert service_provider.startswith('anymail')
        service_provider = service_provider[ len('anymail'): ]
        if service_provider != 'console':
            service_provider = service_provider.upper()
            assert res['EMAIL_HOST_PASSWORD'], f'no api key specified for {service_provider}'
            anymail_settings[ f'{service_provider}_SERVER_TOKEN'] = res['EMAIL_HOST_PASSWORD']
            anymail_settings['WEBHOOK_SECRET'] = env.str('EMAIL_WEBHOOK_SECRET', '')

    if config.get('USE_RQ', False):
        res['RQ_EMAIL_BACKEND'] = res['EMAIL_BACKEND']
        res['EMAIL_BACKEND'] = 'django_rq_email_backend.backends.RQEmailBackend'

    res['EMAIL_USE_NOHTML'] = config.get('USE_NOHTML', False)

    if config.get('USE_FILTER', False):
        res['EMAIL_FILTER_RECIPIENTS'] = dict(
            WHITELIST = env.str('EMAIL_FILTER_WHITELIST', '').split() or None,
            STAFF_ONLY = env.bool('EMAIL_FILTER_STAFF_ONLY', None),
            JOINED_BEFORE = env.date('EMAIL_FILTER_JOINED_BEFORE', None),
            JOINED_AFTER = env.date('EMAIL_FILTER_JOINED_AFTER', None),
            UNKNOWN_USER = env.bool('EMAIL_FILTER_UNKNOWN_USER', None),
            LOGIC = env.str('EMAIL_FILTER_LOGIC', 'or'),
            EMAIL_BACKEND = res['EMAIL_BACKEND'],
        )
        res['EMAIL_BACKEND'] = 'svd_util.django.send_email.FilterEmailBackend'

    res['EMAIL_SUBJECT_PREFIX'] = env.str('EMAIL_SUBJECT_PREFIX', '')
    return res
