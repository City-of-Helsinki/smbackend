import os

import environ
from django.conf.global_settings import LANGUAGES as GLOBAL_LANGUAGES
from django.core.exceptions import ImproperlyConfigured

CONFIG_FILE_NAME = "config_dev.env"


root = environ.Path(__file__) - 2  # two levels back in hierarchy
env = environ.Env(
    DEBUG=(bool, False),
    LANGUAGES=(list, ["fi", "sv", "en"]),
    DATABASE_URL=(str, "postgis:///servicemap"),
    TRUST_X_FORWARDED_HOST=(bool, False),
    SECURE_PROXY_SSL_HEADER=(tuple, None),
    ALLOWED_HOSTS=(list, []),
    SENTRY_DSN=(str, None),
    SENTRY_ENVIRONMENT=(str, "development"),
    COOKIE_PREFIX=(str, "servicemap"),
    INTERNAL_IPS=(list, []),
    CELERY_BROKER_URL=(str, "amqp://guest:guest@localhost:5672"),
    MEDIA_ROOT=(environ.Path(), root("media")),
    STATIC_ROOT=(environ.Path(), root("static")),
    MEDIA_URL=(str, "/media/"),
    STATIC_URL=(str, "/static/"),
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
    CACHE_LOCATION=(str, None),
    TURKU_WFS_URL=(str, None),
    GEO_SEARCH_LOCATION=(str, None),
    GEO_SEARCH_API_KEY=(str, None),
    PTV_ID_OFFSET=(int, None),
    ECO_COUNTER_STATIONS_URL=(str, None),
    ECO_COUNTER_OBSERVATIONS_URL=(str, None),
    GAS_FILLING_STATIONS_IDS=(dict, {}),
    CHARGING_STATIONS_IDS=(dict, {}),
    BICYCLE_STANDS_IDS=(dict, {}),
    BIKE_SERVICE_STATIONS_IDS=(dict, {}),
    AUTORI_SCOPE=(str, None),
    AUTORI_CLIENT_ID=(str, None),
    AUTORI_CLIENT_SECRET=(str, None),
    AUTORI_EVENTS_URL=(str, None),
    AUTORI_ROUTES_URL=(str, None),
    AUTORI_VEHICLES_URL=(str, None),
    AUTORI_CONTRACTS_URL=(str, None),
    AUTORI_TOKEN_URL=(str, None),
    KUNTEC_KEY=(str, None),
)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = root()

# Django environ has a nasty habit of complanining at level
# WARN about env file not being preset. Here we pre-empt it.
env_file_path = os.path.join(BASE_DIR, CONFIG_FILE_NAME)
if os.path.exists(env_file_path):
    # Logging configuration is not available at this point
    print(f"Reading config from {env_file_path}")
    environ.Env.read_env(env_file_path)

DEBUG = env("DEBUG")
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

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
    "django_celery_beat",
    "django_celery_results",
    "munigeo",
    "services.apps.ServicesConfig",
    "observations",
    "eco_counter.apps.EcoCounterConfig",
    "mobility_data.apps.MobilityDataConfig",
    "bicycle_network.apps.BicycleNetworkConfig",
    "iot.apps.IotConfig",
    "street_maintenance.apps.StreetMaintenanceConfig",
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
        "django": {"handlers": ["console"], "level": "INFO"},
        "turku_services_import": {"handlers": ["console"], "level": "DEBUG"},
        "search": {"handlers": ["console"], "level": "INFO"},
        "iot": {"handlers": ["console"], "level": "INFO"},
        "eco_counter": {"handlers": ["console"], "level": "INFO"},
        "mobility_data": {"handlers": ["console"], "level": "INFO"},
        "bicycle_network": {"handlers": ["console"], "level": "INFO"},
        "street_maintenance": {"handlers": ["console"], "level": "INFO"},
    },
}

KML_TRANSLATABLE_FIELDS = ["name", "street_address", "www"]
KML_REGEXP = r"application/vnd.google-earth\.kml"

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

SENTRY_DSN = env("SENTRY_DSN")
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT")

import raven  # noqa

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "default"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_CACHE_BACKEND = "django-cache"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("CACHE_LOCATION"),
    }
}
# Include extended information. i.e. name of the task etc. otherwise the name will be empty in
# version 2.4.0
CELERY_RESULT_EXTENDED = True

# Use in tests with override_settings CACHES = settings.TEST_CACHES
TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}


if SENTRY_DSN:
    RAVEN_CONFIG = {
        "dsn": SENTRY_DSN,
        # Needs to change if settings.py is not in an immediate child of the project
        "release": raven.fetch_git_sha(os.path.dirname(os.pardir)),
        "environment": SENTRY_ENVIRONMENT,
    }


COOKIE_PREFIX = env("COOKIE_PREFIX")
INTERNAL_IPS = env("INTERNAL_IPS")

if "SECRET_KEY" not in locals():
    secret_file = os.path.join(BASE_DIR, ".django_secret")
    try:
        SECRET_KEY = open(secret_file).read().strip()
    except IOError:
        import random

        system_random = random.SystemRandom()
        try:
            SECRET_KEY = "".join(
                [
                    system_random.choice(
                        "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
                    )
                    for i in range(64)
                ]
            )
            secret = open(secret_file, "w")
            import os

            os.chmod(secret_file, 0o0600)
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception(
                "Please create a %s file with random characters to generate your secret key!"
                % secret_file
            )
TURKU_WFS_URL = env("TURKU_WFS_URL")
PTV_ID_OFFSET = env("PTV_ID_OFFSET")
GEO_SEARCH_LOCATION = env("GEO_SEARCH_LOCATION")
GEO_SEARCH_API_KEY = env("GEO_SEARCH_API_KEY")
ECO_COUNTER_OBSERVATIONS_URL = env("ECO_COUNTER_OBSERVATIONS_URL")
ECO_COUNTER_STATIONS_URL = env("ECO_COUNTER_STATIONS_URL")

# Typecast the values to int with listcomprehension.
GAS_FILLING_STATIONS_IDS = {
    k: int(v) for k, v in env("GAS_FILLING_STATIONS_IDS").items()
}
CHARGING_STATIONS_IDS = {k: int(v) for k, v in env("CHARGING_STATIONS_IDS").items()}
BICYCLE_STANDS_IDS = {k: int(v) for k, v in env("BICYCLE_STANDS_IDS").items()}
BIKE_SERVICE_STATIONS_IDS = {
    k: int(v) for k, v in env("BIKE_SERVICE_STATIONS_IDS").items()
}
AUTORI_SCOPE = env("AUTORI_SCOPE")
AUTORI_CLIENT_ID = env("AUTORI_CLIENT_ID")
AUTORI_CLIENT_SECRET = env("AUTORI_CLIENT_SECRET")
AUTORI_EVENTS_URL = env("AUTORI_EVENTS_URL")
AUTORI_ROUTES_URL = env("AUTORI_ROUTES_URL")
AUTORI_VEHICLES_URL = env("AUTORI_VEHICLES_URL")
AUTORI_CONTRACTS_URL = env("AUTORI_CONTRACTS_URL")
AUTORI_TOKEN_URL = env("AUTORI_TOKEN_URL")
KUNTEC_KEY = env("KUNTEC_KEY")
