import os
from pathlib import Path

from django.conf.global_settings import LANGUAGES as GLOBAL_LANGUAGES
from django.core.exceptions import ImproperlyConfigured
from django.utils.log import DEFAULT_LOGGING
from environ import Env

# Enable logging to console from our modules by configuring the root logger
DEFAULT_LOGGING["loggers"][""] = {
    "handlers": ["console"],
    "level": "INFO",
    "propagate": True,
}

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env(
    DEBUG=(bool, False),
    LANGUAGES=(list, ["fi", "sv", "en"]),
    DATABASE_URL=(str, "postgis:///servicemap"),
    SECRET_KEY=(str, "temp_key"),
    TRUST_X_FORWARDED_HOST=(bool, False),
    SECURE_PROXY_SSL_HEADER=(tuple, None),
    ALLOWED_HOSTS=(list, []),
    SENTRY_DSN=(str, None),
    SENTRY_ENVIRONMENT=(str, "development"),
    COOKIE_PREFIX=(str, "servicemap"),
    INTERNAL_IPS=(list, []),
    STATIC_ROOT=(str, str(BASE_DIR / "static")),
    MEDIA_ROOT=(str, str(BASE_DIR / "media")),
    STATIC_URL=(str, "/static/"),
    MEDIA_URL=(str, "/media/"),
    OPEN311_URL_BASE=(str, None),
    OPEN311_API_KEY=(str, None),
    OPEN311_INTERNAL_API_KEY=(str, None),
    OPEN311_SERVICE_CODE=(str, None),
    SHORTCUTTER_UNIT_URL=(str, None),
    ADDRESS_SEARCH_RADIUS=(int, 50),
    TURKU_API_KEY=(str, None),
    ACCESSIBILITY_SYSTEM_ID=(str, None),
    ADDITIONAL_INSTALLED_APPS=(list, None),
    ADDITIONAL_MIDDLEWARE=(list, None),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    IMPORT_LOG_LEVEL=(str, "INFO"),
    SEARCH_LOG_LEVEL=(str, "INFO"),
    GEO_SEARCH_LOCATION=(str, ""),
    GEO_SEARCH_API_KEY=(str, ""),
)

env_path = BASE_DIR / ".env"
if env_path.exists():
    Env.read_env(env_path)

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY")
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
GEO_SEARCH_LOCATION = env("GEO_SEARCH_LOCATION")
GEO_SEARCH_API_KEY = env("GEO_SEARCH_API_KEY")
DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL")
IMPORT_LOG_LEVEL = env("IMPORT_LOG_LEVEL")
SEARCH_LOG_LEVEL = env("SEARCH_LOG_LEVEL")

# Application definition
INSTALLED_APPS = [
    "polymorphic",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.postgres",
    "raven.contrib.django.raven_compat",
    "rest_framework.authtoken",
    "rest_framework",
    "corsheaders",
    "django_extensions",
    "django_filters",
    "modeltranslation",
    "django.contrib.admin",
    "munigeo",
    "services.apps.ServicesConfig",
    "observations",
]

if env("ADDITIONAL_INSTALLED_APPS"):
    INSTALLED_APPS += env("ADDITIONAL_INSTALLED_APPS")

TURKU_API_KEY = env("TURKU_API_KEY")
ACCESSIBILITY_SYSTEM_ID = env("ACCESSIBILITY_SYSTEM_ID")

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

if env("ADDITIONAL_MIDDLEWARE"):
    MIDDLEWARE += env("ADDITIONAL_MIDDLEWARE")

ROOT_URLCONF = "smbackend.urls"
WSGI_APPLICATION = "smbackend.wsgi.application"

# Database
DATABASES = {"default": env.db()}

# Keep the database connection open for 120s
CONN_MAX_AGE = 120

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


def gettext(s):
    return s


# Map language codes to the (code, name) tuples used by Django
# We want to keep the ordering in LANGUAGES configuration variable,
# thus some gyrations
language_map = {x: y for x, y in GLOBAL_LANGUAGES}
try:
    LANGUAGES = tuple((lang, language_map[lang]) for lang in env("LANGUAGES"))
except KeyError as e:
    raise ImproperlyConfigured(f'unknown language code "{e.args[0]}"')
LANGUAGE_CODE = env("LANGUAGES")[0]
MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE

TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_L10N = True
USE_TZ = True

USE_X_FORWARDED_HOST = env("TRUST_X_FORWARDED_HOST")
SECURE_PROXY_SSL_HEADER = env("SECURE_PROXY_SSL_HEADER")
CORS_ORIGIN_ALLOW_ALL = True
TASTYPIE_DEFAULT_FORMATS = ["json"]

DEFAULT_SRID = 3067  # ETRS TM35-FIN
ADDRESS_SEARCH_RADIUS = env("ADDRESS_SEARCH_RADIUS")
# The Finnish national grid coordinates in TM35-FIN according to JHS-180
# specification. We use it as a bounding box.
BOUNDING_BOX = [-548576, 6291456, 1548576, 8388608]
BOUNDING_BOX_WSG84 = [
    10.26199739324485,
    55.61796354326285,
    60.48175983974826,
    72.86779143337851,
]

# If no country specified (for example through a REST API call), use this
# as default.
DEFAULT_COUNTRY = "fi"
# The word used for municipality in the OCD identifiers in the default country.
DEFAULT_OCD_MUNICIPALITY = "kunta"

# Levels are groups or profiles of thematically related services
LEVELS = {
    "common": {
        "type": "include",  # one of: {'exclude', 'include'}
        # The service ids below are either included or excluded according
        # to the type above.
        "service_nodes": [
            991,  # health stations
            1097,  # basic education
            2125,  # pre school education
            869  # municipal day care
            #  25344, # recycling
            #  25480, # public libraries
        ],
    },
    "customer_service": {
        "type": "exclude",
        "service_nodes": [
            2006,  # statues & art
            332,  # wlan hotspots
            530,  # parking vending machines
        ],
    },
}

# Configuration for Open311 feedback forwarding
OPEN311 = {
    "URL_BASE": env("OPEN311_URL_BASE"),
    "API_KEY": env("OPEN311_API_KEY"),
    "INTERNAL_FEEDBACK_API_KEY": env("OPEN311_INTERNAL_API_KEY"),
    "SERVICE_CODE": env("OPEN311_SERVICE_CODE"),
}

# Shortcut generation URL template
SHORTCUTTER_UNIT_URL = env("SHORTCUTTER_UNIT_URL")

# Static & Media files
STATIC_ROOT = env("STATIC_ROOT")
STATIC_URL = env("STATIC_URL")
# This must be changed if STATIC_URL needs to point somewhere that
# does not map to /static/ in the app. The usual mapping of
# /servicemap/static/ is mapped by uwsgi to /static/
# See: http://whitenoise.evans.io/en/stable/django.html#WHITENOISE_STATIC_PREFIX
WHITENOISE_STATIC_PREFIX = "/static/"
MEDIA_ROOT = env("MEDIA_ROOT")
MEDIA_URL = env("MEDIA_URL")

REST_FRAMEWORK = {
    "PAGE_SIZE": 20,
    "DEFAULT_PAGINATION_CLASS": "services.api_pagination.Pagination",
    "URL_FIELD_NAME": "resource_uri",
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "observations.models.PluralityTokenAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "rest_framework_jsonp.renderers.JSONPRenderer",
    ),
    "EXCEPTION_HANDLER": "services.exceptions.api_exception_handler",
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    },
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamped_named": {
            "format": "%(asctime)s %(name)s %(levelname)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "timestamped_named",
        },
        # Just for reference, not used
        "blackhole": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": DJANGO_LOG_LEVEL},
        "search": {"handlers": ["console"], "level": SEARCH_LOG_LEVEL},
        "import": {"handlers": ["console"], "level": IMPORT_LOG_LEVEL},
    },
}

KML_TRANSLATABLE_FIELDS = ["name", "street_address", "www"]
KML_REGEXP = r"application/vnd.google-earth\.kml"

LOCALE_PATHS = (str(BASE_DIR / "locale"),)

SENTRY_DSN = env("SENTRY_DSN")
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT")

import raven  # noqa

if SENTRY_DSN:
    RAVEN_CONFIG = {
        "dsn": SENTRY_DSN,
        # Needs to change if settings.py is not in an immediate child of the project
        "release": raven.fetch_git_sha(os.path.dirname(os.pardir)),
        "environment": SENTRY_ENVIRONMENT,
    }


COOKIE_PREFIX = env("COOKIE_PREFIX")
INTERNAL_IPS = env("INTERNAL_IPS")
