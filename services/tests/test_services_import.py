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

FIELD_MAPPINGS = {
    'desc': 'description',
    'short_desc': 'short_description',
}


def api_field_value(dest, name):
    return dest[FIELD_MAPPINGS.get(name, name)]


def assert_field_exists(name, src, dest):
    if src.get(name) is None:
        assert api_field_value(dest, name) is None
    else:
        assert name in dest


def assert_field_match(name, src, dest):
    assert_field_exists(name, src, dest)
    assert src[name] == api_field_value(dest, name)


def assert_string_field_match(name, src, dest):
    assert_field_exists(name, src, dest)
    if src[name] is None:
        assert api_field_value(dest, name) is None
        return
    val = src[name].replace('\u0000', ' ')
    if len(val.split()) == 0:
        assert api_field_value(dest, name) is None
    else:
        assert val.split() == api_field_value(dest, name).split(), \
            "{}: '{}' does not match '{}'".format(name, src[name], api_field_value(dest, name))


def assert_translated_field_match(name, src, dest):
    for lang in LANGUAGES:
        s = src['{}_{}'.format(name, lang)].replace('\u0000', ' ')
        assert api_field_value(dest, name) is not None, '{} is none'.format(name)
        d = api_field_value(dest, name)[lang]
        if s is None or len(s) == 0:
            assert d is None
            return
        # compare ignoring whitespace and empty bytes
        assert s.split() == d.split()


def assert_unit_correctly_imported(unit, source_unit):
    d = unit
    s = source_unit

    assert_field_match('id', s, d)
    assert_string_field_match('accessibility_email', s, d)

    for field_name in [
            'address_postal_full',
            'call_charge_info',
            'desc',
            'name',
            'picture_caption',
            'short_desc',
            'street_address',
            'www']:
        assert_translated_field_match(field_name, s, d)

    assert d['municipality'] == s['address_city_fi'].lower()  # IMPROVE SPEC

    # TODO: look for extra_searchwords -> keywords

    # string
    # ======
    # 'accessibility_email'
    # 'accessibility_phone'
    # 'accessibility_viewpoints'
    # 'accessibility_www'
    # 'address_zip'
    # 'data_source_url'
    # 'dept_id'
    # 'email'
    # 'fax'
    # 'phone'
    # 'organizer_business_id'

    # ?
    # 'id'

    # 'modified_time'
    # 'created_time'

    # 'easting_etrs_gk25'
    # 'easting_etrs_tm35fin'
    # 'northing_etrs_gk25'
    # 'northing_etrs_tm35fin'
    # 'latitude'
    # 'longitude'

    # 'manual_coordinates'

    # 'ontologytree_ids'
    # 'ontologyword_ids'

    # 'organizer_type'

    # 'org_id'
    # 'picture_entrance_url'
    # 'picture_url'
    # 'provider_type'
    # 'source'
    # 'sources'
    # 'streetview_entrance_url'



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
