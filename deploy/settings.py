import smbackend.settings

# Get whitenoise for serving static files
try:
    place = smbackend.settings.MIDDLEWARE.index(
        "django.middleware.security.SecurityMiddleware"
    )
except ValueError:
    place = 0

smbackend.settings.MIDDLEWARE.insert(
    place, "whitenoise.middleware.WhiteNoiseMiddleware"
)
