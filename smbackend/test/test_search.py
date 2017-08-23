import pytest
import django.utils.translation
from django.core.management import call_command
from django.test import Client
from django.test import override_settings
from haystack.query import SearchQuerySet
import haystack
import elasticsearch

from .conftest import TEST_INDEX


connection_available = None
backend = haystack.connections['default'].get_backend()
try:
    backend.update('servicemap-fi', [])
    connection_available = True
except elasticsearch.exceptions.ConnectionError as e:
    connection_available = False


@pytest.mark.skipif(not connection_available, reason='Search backend unavailable')
@pytest.mark.django_db
def test_search(haystack_test, db_content):
    django.utils.translation.activate('fi')

    # Check that we find all we need via search
    # (for some reason Units are not indexed with working `object` reference, works with Services though)
    assert db_content['unit'].name in SearchQuerySet().filter(text='kirjasto')[0].text
    assert SearchQuerySet().filter(text='kirjasto')[1].object.name == db_content['service'].name

    # No results for something that is not there
    assert len(SearchQuerySet().filter(text='sairaala')) == 0


@pytest.mark.skipif(connection_available is False, reason='Search backend unavailable')
@pytest.mark.django_db
def test_search_filters(haystack_test, db_content):
    c = Client()
    resp = c.get('/v1/search/', {'q': 'kirjasto'})
    assert resp.status_code == 200
    assert db_content['unit'].name in str(resp.content)
    resp = c.get('/v1/search/', {'q': 'kirjasto', 'only': 'services.service'})
    assert db_content['unit'].name not in str(resp.content)
    # check for #38, don't fail if dot-format not used in only
    resp = c.get('/v1/search/', {'q': 'kirjasto', 'only': 'unit'})
    assert db_content['unit'].name not in str(resp.content)  # won't return any content, fail with a log entry
