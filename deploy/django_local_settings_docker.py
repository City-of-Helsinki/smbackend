import environ
import raven

# This is expected to be in project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = environ.Path(BASE_DIR)

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ''),
    ALLOWED_HOSTS=(list, []),
    ADMINS=(list, []),
    DATABASE_URL=(str, 'postgis:///smbackend'),
    JWT_SECRET_KEY=(str, ''),
    JWT_AUDIENCE=(str, ''),
    MEDIA_ROOT=(environ.Path(), root('media')),
    STATIC_ROOT=(environ.Path(), root('static')),
    MEDIA_URL=(str, '/media/'),
    STATIC_URL=(str, '/static/'),
    LOGIN_REDIRECT_URL=(str, '/admin'),
    SENTRY_DSN=(str, ''),
    SENTRY_ENVIRONMENT=(str,''),
    COOKIE_PREFIX=(str, 'smbackend'),
    TRUST_X_FORWARDED_HOST=(bool, False),
)

DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')
ADMINS = env('ADMINS')

DATABASES = {
    'default': env.db('DATABASE_URL')
}

MEDIA_ROOT = env('MEDIA_ROOT')
MEDIA_URL = env('MEDIA_URL')

STATIC_ROOT = env('STATIC_ROOT')
STATIC_URL = env('STATIC_URL')

LOGIN_REDIRECT_URL = env('LOGIN_REDIRECT_URL')

SENTRY_DSN = env('SENTRY_DSN')

RAVEN_CONFIG = {
    'dsn': env('SENTRY_DSN'),
    'environment': env('SENTRY_ENVIRONMENT'),
    'release': raven.fetch_git_sha(BASE_DIR),
}

CSRF_COOKIE_NAME = '{}-csrftoken'.format(env('COOKIE_PREFIX'))
CSRF_COOKIE_PATH = '/{}'.format(env('COOKIE_PREFIX'))
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_NAME = '{}-sessionid'.format(env('COOKIE_PREFIX'))
SESSION_COOKIE_PATH = '/{}'.format(env('COOKIE_PREFIX'))
SESSION_COOKIE_SECURE = True

USE_X_FORWARDED_HOST = env('TRUST_X_FORWARDED_HOST')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

# Django default logging without debug does not output anything
# to std*, let use log errors and worse. They should end up
# in the runtime (ie. uwsgi) logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
}
