"""
Django settings for smbackend project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'hh!*t_%#ql6v3juo5usfry1m&t)9w@b+_y@u%0h$x742c18n!a'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'corsheaders',
    'django_extensions',
    'modeltranslation',

    'munigeo',
    'services',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

gettext = lambda s: s
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

PROJECTION_SRID = 3067 # ETRS TM35-FIN
# The Finnish national grid coordinates in TM35-FIN according to JHS-180
# specification. We use it as a bounding box.
BOUNDING_BOX = [-548576, 6291456, 1548576, 8388608]

# If no country specified (for example through a REST API call), use this
# as default.
DEFAULT_COUNTRY = 'fi'
# The word used for municipality in the OCD identifiers in the default country.
DEFAULT_OCD_MUNICIPALITY = 'kunta'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'PAGINATE_BY': 20,
    'URL_FIELD_NAME': 'resource_uri',
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',)
}

try:
    from local_settings import *
except ImportError:
    pass
