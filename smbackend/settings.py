import logging.config
import os
from pathlib import Path

import sentry_sdk
from corsheaders.defaults import default_headers
from csp.constants import NONCE, NONE, SELF
from django.conf.global_settings import LANGUAGES as GLOBAL_LANGUAGES
from django.core.exceptions import ImproperlyConfigured
from environ import Env
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.types import SamplingContext

GDAL_LIBRARY_PATH = os.environ.get("GDAL_LIBRARY_PATH")
GEOS_LIBRARY_PATH = os.environ.get("GEOS_LIBRARY_PATH")

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env(
    DEBUG=(bool, False),
    LANGUAGES=(list, ["fi", "sv", "en"]),
    DATABASE_URL=(str, "postgis:///servicemap"),
    DATABASE_PASSWORD=(str, ""),
    SECRET_KEY=(str, ""),
    TRUST_X_FORWARDED_HOST=(bool, False),
    SECURE_PROXY_SSL_HEADER=(tuple, None),
    ALLOWED_HOSTS=(list, []),
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, "local"),
    SENTRY_PROFILE_SESSION_SAMPLE_RATE=(float, None),
    SENTRY_RELEASE=(str, None),
    SENTRY_TRACES_SAMPLE_RATE=(float, None),
    SENTRY_TRACES_IGNORE_PATHS=(list, ["/healthz", "/readiness"]),
    COOKIE_PREFIX=(str, "servicemap"),
    INTERNAL_IPS=(list, []),
    STATIC_ROOT=(str, str(BASE_DIR / "static")),
    MEDIA_ROOT=(str, str(BASE_DIR / "media")),
    STATIC_URL=(str, "/static/"),
    MEDIA_URL=(str, "/media/"),
    OPEN311_NEW_SERVICE_ENABLED=(bool, False),
    OPEN311_URL_BASE=(str, None),
    OPEN311_API_KEY=(str, None),
    OPEN311_INTERNAL_API_KEY=(str, None),
    OPEN311_SERVICE_CODE=(str, None),
    SHORTCUTTER_UNIT_URL=(str, None),
    ADDRESS_SEARCH_RADIUS=(int, 50),
    ADDITIONAL_MIDDLEWARE=(list, None),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    IMPORT_LOG_LEVEL=(str, "INFO"),
    SEARCH_LOG_LEVEL=(str, "INFO"),
    GEO_SEARCH_LOCATION=(str, ""),
    GEO_SEARCH_API_KEY=(str, ""),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_HOST=(str, None),
    EMAIL_PORT=(int, None),
    EMAIL_TIMEOUT=(int, None),
    EMAIL_HOST_USER=(str, None),
    EMAIL_HOST_PASSWORD=(str, None),
    OTP_EMAIL_SENDER=(str, None),
    PICTURE_URL_REWRITE_ENABLED=(bool, False),
    CSP_ENABLED=(bool, False),
    CSP_REPORT_ONLY=(bool, True),
    CSP_REPORT_URI=(str, None),
    IMPORT_DATA_PATH=(str, None),
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
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_TIMEOUT = env("EMAIL_TIMEOUT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
OTP_EMAIL_SENDER = env("OTP_EMAIL_SENDER")
PICTURE_URL_REWRITE_ENABLED = env("PICTURE_URL_REWRITE_ENABLED")
IMPORT_DATA_PATH = env("IMPORT_DATA_PATH")

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
    "drf_spectacular",
    # Two-factor authentication
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_email",
    "two_factor",
    "two_factor.plugins.email",
    "logger_extra",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "logger_extra.middleware.XRequestIdMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django_otp.middleware.OTPMiddleware",
]

if env("ADDITIONAL_MIDDLEWARE"):
    MIDDLEWARE += env("ADDITIONAL_MIDDLEWARE")


if env("CSP_ENABLED"):
    INSTALLED_APPS.append("csp")
    MIDDLEWARE.append("csp.middleware.CSPMiddleware")


ROOT_URLCONF = "smbackend.urls"
WSGI_APPLICATION = "smbackend.wsgi.application"

# Database
DATABASES = {"default": env.db()}

if env("DATABASE_PASSWORD"):
    DATABASES["default"]["PASSWORD"] = env("DATABASE_PASSWORD")

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
USE_TZ = True

USE_X_FORWARDED_HOST = env("TRUST_X_FORWARDED_HOST")
SECURE_PROXY_SSL_HEADER = env("SECURE_PROXY_SSL_HEADER")
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = (
    *default_headers,
    "baggage",
    "sentry-trace",
)
TASTYPIE_DEFAULT_FORMATS = ["json"]

DEFAULT_SRID = 3067  # ETRS TM35-FIN
PROJECTION_SRID = 3067
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
            869,  # municipal day care
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
    "NEW_SERVICE_ENABLED": env("OPEN311_NEW_SERVICE_ENABLED"),
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
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
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
    "filters": {
        "context": {
            "()": "logger_extra.filter.LoggerContextFilter",
        }
    },
    "formatters": {
        "json": {
            "()": "logger_extra.formatter.JSONFormatter",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["context"],
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": DJANGO_LOG_LEVEL},
        "services.search": {"handlers": ["console"], "level": SEARCH_LOG_LEVEL},
        "services.management": {"handlers": ["console"], "level": IMPORT_LOG_LEVEL},
        "two_factor": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

logging.config.dictConfig(LOGGING)

KML_TRANSLATABLE_FIELDS = ["name", "street_address", "www"]
KML_REGEXP = r"application/vnd.google-earth\.kml"

LOCALE_PATHS = (str(BASE_DIR / "locale"),)

SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE")
SENTRY_TRACES_IGNORE_PATHS = env.list("SENTRY_TRACES_IGNORE_PATHS")


def sentry_traces_sampler(sampling_context: SamplingContext) -> float:
    # Respect parent sampling decision if one exists. Recommended by Sentry.
    if (parent_sampled := sampling_context.get("parent_sampled")) is not None:
        return float(parent_sampled)

    # Exclude health check endpoints from tracing
    path = sampling_context.get("wsgi_environ", {}).get("PATH_INFO", "")
    if path.rstrip("/") in SENTRY_TRACES_IGNORE_PATHS:
        return 0

    # Use configured sample rate for all other requests
    return SENTRY_TRACES_SAMPLE_RATE or 0


if env("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=env.str("SENTRY_DSN"),
        environment=env.str("SENTRY_ENVIRONMENT"),
        release=env.str("SENTRY_RELEASE"),
        integrations=[DjangoIntegration()],
        traces_sampler=sentry_traces_sampler,
        profile_session_sample_rate=env.str("SENTRY_PROFILE_SESSION_SAMPLE_RATE"),
        profile_lifecycle="trace",
    )

COOKIE_PREFIX = env("COOKIE_PREFIX")
INTERNAL_IPS = env("INTERNAL_IPS")

SPECTACULAR_SETTINGS = {
    "TITLE": "Palvelukartta REST API",
    "DESCRIPTION": "Backend service for the Service Map UI.",
    "VERSION": "v2",
    "CONTACT": {
        "name": "City of Helsinki",
        "url": "https://www.hel.fi",
    },
    "LICENSE": {
        "name": "AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
    "SERVE_INCLUDE_SCHEMA": False,
}

# Two-factor authentication settings
LOGIN_URL = "two_factor:login"
OTP_EMAIL_SUBJECT = "Palvelukartta - kirjautumistunniste"

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"


content_security_policy_configuration = {
    "EXCLUDE_URL_PREFIXES": ["/excluded-path/"],
    "DIRECTIVES": {
        "default-src": [NONE],
        "connect-src": [SELF],
        "img-src": [SELF],
        "form-action": [SELF],
        "frame-ancestors": [SELF],
        "script-src": [
            SELF,
            "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.5.2/js/bootstrap.min.js",
        ],
        "style-src": [
            SELF,
            NONCE,
            "https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.5.2/css/bootstrap.min.css",
        ],
        "upgrade-insecure-requests": True,
    },
}

if report_uri := env("CSP_REPORT_URI"):
    content_security_policy_configuration["DIRECTIVES"]["report-uri"] = report_uri

if env("CSP_REPORT_ONLY"):
    CONTENT_SECURITY_POLICY = None
    CONTENT_SECURITY_POLICY_REPORT_ONLY = content_security_policy_configuration

else:
    CONTENT_SECURITY_POLICY = content_security_policy_configuration
    CONTENT_SECURITY_POLICY_REPORT_ONLY = None
