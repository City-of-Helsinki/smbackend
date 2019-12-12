import json
import os

from django.conf.global_settings import LANGUAGES as GLOBAL_LANGUAGES
from django.core.exceptions import ImproperlyConfigured
import environ

CONFIG_FILE_NAME = "config_dev.env"


root = environ.Path(__file__) - 2  # two levels back in hierarchy
env = environ.Env(
    DEBUG=(bool, False),
    LANGUAGES=(list, ['fi', 'sv', 'en']),
    DATABASE_URL=(str, 'postgis:///servicemap'),
    ELASTICSEARCH_URL=(str, None),
    DISABLE_HAYSTACK_SIGNAL_PROCESSOR=(bool, False),
    ALLOWED_HOSTS=(list, []),
    SENTRY_DSN=(str, ''),
    SENTRY_ENVIRONMENT=(str, 'development'),
    COOKIE_PREFIX=(str, 'servicemap'),
    INTERNAL_IPS=(list, []),
    MEDIA_ROOT=(environ.Path(), root('media')),
    STATIC_ROOT=(environ.Path(), root('static')),
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = root()

# Django environ has a nasty habit of complanining at level
# WARN about env file not being preset. Here we pre-empt it.
env_file_path = os.path.join(BASE_DIR, CONFIG_FILE_NAME)
if os.path.exists(env_file_path):
    # Logging configuration is not available at this point
    print(f'Reading config from {env_file_path}')
    environ.Env.read_env(env_file_path)

DEBUG = env('DEBUG')
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

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
    'observations',
)

MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smbackend.urls'
WSGI_APPLICATION = 'smbackend.wsgi.application'

# Database
DATABASES = {
    'default': env.db()
}

# Keep the database connection open for 120s
CONN_MAX_AGE = 120


def gettext(s):
    return s


# Map language codes to the (code, name) tuples used by Django
# We want to keep the ordering in LANGUAGES configuration variable,
# thus some gyrations
language_map = {x: y for x, y in GLOBAL_LANGUAGES}
try:
    LANGUAGES = tuple((l, language_map[l]) for l in env('LANGUAGES'))
except KeyError as e:
    raise ImproperlyConfigured(f"unknown language code \"{e.args[0]}\"")
LANGUAGE_CODE = env('LANGUAGES')[0]
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
        'service_nodes': [
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
        'service_nodes': [
            2006,  # statues & art
            332,   # wlan hotspots
            530    # parking vending machines
        ]
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
MEDIA_ROOT = env('MEDIA_ROOT')
STATIC_ROOT = env('STATIC_ROOT')

REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'DEFAULT_PAGINATION_CLASS': 'services.api_pagination.Pagination',
    'URL_FIELD_NAME': 'resource_uri',
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
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


def read_config(name):
    return json.load(open(
        os.path.join(
            BASE_DIR,
            'smbackend',
            'elasticsearch/{}.json'.format(name))))


def haystack_connection_for_lang(language_code):
    if language_code == "fi":
        return {
            'default-fi': {
                'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
                'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
                'URL': env('ELASTICSEARCH_URL'),
                'INDEX_NAME': 'servicemap-fi',
                'MAPPINGS': read_config('mappings_finnish')['modelresult']['properties'],
                'SETTINGS': read_config('settings_finnish')
            }
        }
    else:
        return {
            f'default-{language_code}': {
                'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
                'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
                'URL': env('ELASTICSEARCH_URL'),
                'INDEX_NAME': f'servicemap-{language_code}'
            }
        }


def dummy_haystack_connection_for_lang(language_code):
    return {
        f'default-{language_code}': {
            'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
            'BASE_ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
        }
    }


HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'multilingual_haystack.backends.MultilingualSearchEngine',
    }
}

for language in [l[0] for l in LANGUAGES]:
    if env('ELASTICSEARCH_URL'):
        connection = haystack_connection_for_lang(language)
    else:
        connection = dummy_haystack_connection_for_lang(language)
    HAYSTACK_CONNECTIONS.update(connection)


HAYSTACK_LIMIT_TO_REGISTERED_MODELS = False
HAYSTACK_SIGNAL_PROCESSOR = 'services.search_indexes.DeleteOnlySignalProcessor'
DISABLE_HAYSTACK_SIGNAL_PROCESSOR = env('DISABLE_HAYSTACK_SIGNAL_PROCESSOR')

KML_TRANSLATABLE_FIELDS = ['name', 'street_address', 'www']
KML_REGEXP = r'application/vnd.google-earth\.kml'

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
            SECRET_KEY = ''.join([system_random.choice(
                'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(64)])
            secret = open(secret_file, 'w')
            import os
            os.chmod(secret_file, 0o0600)
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception('Please create a %s file with random characters to generate your secret key!' % secret_file)
