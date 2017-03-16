import pytest
import django.utils.translation
from django.core.management import call_command
from django.test import override_settings
from haystack.query import SearchQuerySet

from .conftest import TEST_INDEX


@pytest.mark.django_db
def test_search(haystack_test, db_content):
    call_command('update_index', interactive=False, verbosity=0)

    django.utils.translation.activate('fi')

    # Check that we find all we need via search
    # (for some reason Units are not indexed with working `object` reference, works with Services though)
    assert db_content['unit'].name in SearchQuerySet().all().filter(text='kirjasto')[0].text
    assert SearchQuerySet().all().filter(text='kirjasto')[1].object.name == db_content['service'].name

    # No results for something that is not there
    assert len(SearchQuerySet().all().filter(text='sairaala')) == 0


