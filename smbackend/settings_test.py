from .settings import *

# Not needed in tests, slows processing
DISABLE_HAYSTACK_SIGNAL_PROCESSOR = True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'HOST': '127.0.0.1',
        'NAME': 'smbackend',
        'USER': 'smbackend',
        'PASSWORD': 'smbackend',
    }
}
