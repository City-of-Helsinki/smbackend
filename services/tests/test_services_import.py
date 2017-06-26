from hypothesis import given
from hypothesis.strategies import lists
import pytest
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

# from services.management.commands.services_import.services import import_services
from services.management.commands.services_import.organizations import import_organizations
from services.management.commands.services_import.departments import import_departments
from services.management.commands.services_import.units import import_units

from services_import_hypothesis import closed_object_set


def get(api_client, url, data=None):
    response = api_client.get(url, data=data, format='json')
    assert response.status_code == 200, str(response.content)
    return response


@pytest.fixture
def api_client():
    return APIClient()

LANGUAGES = ['fi', 'sv', 'en']


def assert_field_match(name, src, dest):
    if src[name] == '':
        assert dest[name] is None
    else:
        assert src[name] == dest[name]


def assert_translated_field_match(name, src, dest):
    for lang in LANGUAGES:
        s = src['name_{}'.format(lang)].replace('\u0000', ' ')
        d = dest[name][lang]
        # compare ignoring whitespace and empty bytes
        assert s.split() == d.split()


def assert_unit_correctly_imported(unit, source_unit):
    d = unit
    s = source_unit

    assert_field_match('id', s, d)
    assert_field_match('accessibility_email', s, d)

    assert_translated_field_match('name', s, d)
    # 'accessibility_email'
    # 'accessibility_phone'
    # 'accessibility_viewpoints'
    # 'accessibility_www'
    # 'address_city_en'
    # 'address_city_fi'
    # 'address_city_sv'
    # 'address_postal_full_en'
    # 'address_postal_full_fi'
    # 'address_postal_full_sv'
    # 'address_zip'
    # 'call_charge_info_en'
    # 'call_charge_info_fi'
    # 'call_charge_info_sv'
    # 'created_time'
    # 'data_source_url'
    # 'dept_id'
    # 'desc_en'
    # 'desc_fi'
    # 'desc_sv'
    # 'easting_etrs_gk25'
    # 'easting_etrs_tm35fin'
    # 'email'
    # 'extra_searchwords_en'
    # 'extra_searchwords_fi'
    # 'extra_searchwords_sv'
    # 'fax'
    # 'id'
    # 'latitude'
    # 'longitude'
    # 'manual_coordinates'
    # 'modified_time'
    # 'name_en'
    # 'name_fi'
    # 'name_sv'
    # 'northing_etrs_gk25'
    # 'northing_etrs_tm35fin'
    # 'ontologytree_ids'
    # 'ontologyword_ids'
    # 'organizer_business_id'
    # 'organizer_type'
    # 'org_id'
    # 'phone'
    # 'picture_caption_en'
    # 'picture_caption_fi'
    # 'picture_caption_sv'
    # 'picture_entrance_url'
    # 'picture_url'
    # 'provider_type'
    # 'short_desc_en'
    # 'short_desc_fi'
    # 'short_desc_sv'
    # 'source'
    # 'sources'
    # 'street_address_en'
    # 'street_address_fi'
    # 'street_address_sv'
    # 'streetview_entrance_url'
    # 'www_en'
    # 'www_fi'
    # 'www_sv'


@pytest.mark.django_db
@given(lists(closed_object_set()))
def test_import_units(api_client, all_resources):

    for resources in all_resources:
        def fetch_resource(name):
            return resources.get(name, set())

        def fetch_units():
            return fetch_resource('unit')

        org_syncher = import_organizations(fetch_resource=fetch_resource)
        dept_syncher = import_departments(fetch_resource=fetch_resource)

        import_units(
            fetch_units=fetch_units, fetch_resource=fetch_resource,
            org_syncher=org_syncher, dept_syncher=dept_syncher)

        response = get(api_client, reverse('unit-list'))

        # The API-exposed unit count must exactly equal the original
        # import source unit count.
        assert response.data['count'] == len(resources['unit'])

        def id_set(units):
            return set((u['id'] for u in units))

        result_units = response.data['results']

        # The ids in source and result must exactly match
        assert (id_set(result_units) ==
                id_set(resources['unit']))

        source_units_by_id = dict((u['id'], u) for u in resources['unit'])

        for unit in result_units:
            assert_unit_correctly_imported(unit, source_units_by_id.get(unit['id']))
