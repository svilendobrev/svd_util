DEBUG = True
DEBUG_SQL = 0   #instead of this, for tests use ... --debug-sql
SECRET_KEY = '123'
#DATABASE_URL = 'sqlite:////home/tmp/tapql.db'
DATABASES = dict(
    default= dict(
        ENGINE  = 'django.db.backends.sqlite3',
        NAME    = '/home/tmp/tapl.db',
    ))
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',

    'graphene_django',      #also mngmt: graphql_schema
    'svd_util.grafql.tapql'
    ]
#AUTH_USER_MODEL = 'tapql.User'
ROOT_URLCONF = 'svd_util.grafql.tapql.tapi'
ALLOWED_HOSTS = ['*']
