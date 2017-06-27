"""
Django settings for smbackend project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'hh!*t_%#ql6v3juo5usfry1m&t)9w@b+_y@u%0h$x742c18n!a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'polymorphic',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.postgres',
    'raven.contrib.django.raven_compat',
    'rest_framework.authtoken',
    'rest_framework',
    'corsheaders',
    'django_extensions',
    'django_filters',
    'modeltranslation',
    'haystack',
    'munigeo',
    'services',
    'observations'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'profiler.middleware.ProfilerMiddleware',
)

ROOT_URLCONF = 'smbackend.urls'

WSGI_APPLICATION = 'smbackend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Keep the database connection open for 120s
CONN_MAX_AGE = 120

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/


def gettext(s):
    return s
LANGUAGES = (
    ('fi', gettext('Finnish')),
    ('sv', gettext('Swedish')),
    ('en', gettext('English')),

)
LANGUAGE_CODE = 'fi'
MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE

TIME_ZONE = 'Europe/Helsinki'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CORS_ORIGIN_ALLOW_ALL = True
TASTYPIE_DEFAULT_FORMATS = ['json']

DEFAULT_SRID = 3067  # ETRS TM35-FIN
# The Finnish national grid coordinates in TM35-FIN according to JHS-180
# specification. We use it as a bounding box.
BOUNDING_BOX = [-548576, 6291456, 1548576, 8388608]

# If no country specified (for example through a REST API call), use this
# as default.
DEFAULT_COUNTRY = 'fi'
# The word used for municipality in the OCD identifiers in the default country.
DEFAULT_OCD_MUNICIPALITY = 'kunta'

# Levels are groups or profiles of thematically related services
LEVELS = {
    'common': {
        'type': 'include',  # one of: {'exclude', 'include'}
        # The service ids below are either included or excluded according
        # to the type above.
        'services': [
            991,   # health stations
            1097,  # basic education
            2125,  # pre school education
            869    # municipal day care
            #  25344, # recycling
            #  25480, # public libraries
         ]
    },
    'customer_service': {
        'type': 'exclude',
        'services': [
            2006,  # statues & art
            332,   # wlan hotspots
            530    # parking vending machines
        ]
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'DEFAULT_PAGINATION_CLASS': 'services.api_pagination.Pagination',
    'URL_FIELD_NAME': 'resource_uri',
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'observations.models.PluralityTokenAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_jsonp.renderers.JSONPRenderer'
    ),
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
    },
    'default-fi': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
    },
    'default-en': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
    },
    'default-sv': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
    }
}

HAYSTACK_LIMIT_TO_REGISTERED_MODELS = False
HAYSTACK_SIGNAL_PROCESSOR = 'services.search_indexes.DeleteOnlySignalProcessor'

KML_TRANSLATABLE_FIELDS = ['name', 'street_address', 'www']
KML_REGEXP = 'application/vnd.google-earth\.kml'

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
f = os.path.join(BASE_DIR, "local_settings.py")
if os.path.exists(f):
    import sys
    import imp
    module_name = "%s.local_settings" % ROOT_URLCONF.split('.')[0]
    module = imp.new_module(module_name)
    module.__file__ = f
    sys.modules[module_name] = module
    exec(open(f, "rb").read())

if 'SECRET_KEY' not in locals():
    secret_file = os.path.join(BASE_DIR, '.django_secret')
    try:
        SECRET_KEY = open(secret_file).read().strip()
    except IOError:
        import random
        system_random = random.SystemRandom()
        try:
            SECRET_KEY = ''.join([system_random.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(64)])
            secret = open(secret_file, 'w')
            import os
            os.chmod(secret_file, 0o0600)
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception('Please create a %s file with random characters to generate your secret key!' % secret_file)
