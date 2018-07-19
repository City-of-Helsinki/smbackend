import environ

env = environ.Env()

INSTANCE_NAME = env.str('INSTANCE_NAME', default="smbackend")
URL_PREFIX = '/' + env.str('URL_PREFIX', default="")

LOGIN_REDIRECT_URL = 'https://api.hel.fi{}/admin/'.format(URL_PREFIX)
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

CSRF_COOKIE_NAME = '{}-csrftoken'.format(INSTANCE_NAME)
CSRF_COOKIE_PATH = '{}'.format(URL_PREFIX)
SESSION_COOKIE_NAME = '{}-sessionid'.format(INSTANCE_NAME)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_PATH = '{}'.format(URL_PREFIX)

SITE_TYPE = env.str('SITE_STATE', default="dev")

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

STATIC_ROOT = '/opt/smbackend/static'
MEDIA_ROOT = '/opt/smbackend/media'
STATIC_URL = '{}/static/'.format(URL_PREFIX)
MEDIA_URL = '{}/media/'.format(URL_PREFIX)
