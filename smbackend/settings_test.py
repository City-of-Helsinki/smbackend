import json
import os

from .settings import *


del HAYSTACK_SIGNAL_PROCESSOR


def read_config(name):
    return json.load(open(
        os.path.join(
            BASE_DIR,
            'smbackend',
            'elasticsearch/{}.json'.format(name))))


HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'multilingual_haystack.backends.MultilingualSearchEngine',
    },
    'default-fi': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-fi',
        'MAPPINGS': read_config('mappings_finnish')['modelresult']['properties'],
        'SETTINGS': read_config('settings_finnish')
    },
    'default-sv': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-sv',
    },
    'default-en': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-en',
    },
}
