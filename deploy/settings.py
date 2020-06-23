import smbackend.settings

# Get whitenoise for serving static files
try:
    place = smbackend.settings.MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
except ValueError:
    place = 0

smbackend.settings.MIDDLEWARE.insert(place, 'whitenoise.middleware.WhiteNoiseMiddleware')


deploy_env = smbackend.settings.environ.Env(
    USE_X_FORWARDED_HOST=(bool, False),
    SECURE_PROXY=(bool, False),
    MEDIA_ROOT=(str, "/usr/src/app/www")
)

USE_X_FORWARDED_HOST = deploy_env('USE_X_FORWARDED_HOST')

if deploy_env('SECURE_PROXY'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
