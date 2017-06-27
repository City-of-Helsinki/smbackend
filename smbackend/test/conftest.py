import os
import json
import pytest
import haystack
from django.utils import timezone
from django.conf import settings
from django.core.management import call_command
from services.models import Unit, UnitConnection, Organization, OntologyWord


def read_config(name):
    return json.load(open(
        os.path.join(
            settings.BASE_DIR,
            'elasticsearch/{}.json'.format(name))))


TEST_INDEX = {
    'default': {
        'ENGINE': 'multilingual_haystack.backends.MultilingualSearchEngine',
    },
    'default-fi': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-fi-test',
        'MAPPINGS': read_config('mappings_finnish')['modelresult']['properties'],
        'SETTINGS': read_config('settings_finnish')
    },
    'default-sv': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-sv-test',
    },
    'default-en': {
        'ENGINE': 'multilingual_haystack.backends.LanguageSearchEngine',
        'BASE_ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'servicemap-en-test',
    },
}


@pytest.fixture
def haystack_test():
    """ Set up testing haystack. """
    settings.HAYSTACK_CONNECTIONS = TEST_INDEX
    haystack.connections.reload('default')
    yield haystack
    call_command('clear_index', interactive=False, verbosity=0)


@pytest.fixture
def db_content():
    """ Generate some content to test against """
    s = OntologyWord(id=1, name='Kirjasto', unit_count=0, last_modified_time=timezone.now())
    s.save()
    o = Organization(id=1, name="Helsingin kaupunki")
    o.save()
    u = Unit(id=27586,
             provider_type=1,
             organization=o,
             origin_last_modified_time=timezone.now(),
             name='Kallion kirjasto',
             description='Kirjasto kallion keskustassa',
             street_address='Arentikuja 3')
    u.save()
    u.services.add(s)
    uc = UnitConnection(unit=u, name='John Doe', phone='040 123 1234', type=999)
    uc.save()
    call_command('update_index', interactive=False, verbosity=0)
    return {'service': s, 'unit': u}
