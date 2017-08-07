from hypothesis import given, settings
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


def assert_dest_field_exists(name, src, dest):
    if src.get(name) is None:
        assert api_field_value(dest, name) is None
    else:
        assert name in dest


def assert_field_match(name, src, dest, required=False):
    assert not required or name in src

    assert_dest_field_exists(name, src, dest)
    assert src[name] == api_field_value(dest, name)


def assert_string_field_match(name, src, dest, required=False):
    assert not required or name in src

    assert_dest_field_exists(name, src, dest)
    if src.get(name) is None:
        assert api_field_value(dest, name) is None
        return

    val = src[name].replace('\u0000', ' ')
    if len(val.split()) == 0:
        assert api_field_value(dest, name) is None
    else:
        assert val.split() == api_field_value(dest, name).split(), \
            "{}: '{}' does not match '{}'".format(name, src[name], api_field_value(dest, name))


def assert_translated_field_match(name, src, dest):
    val = api_field_value(dest, name)
    for lang in LANGUAGES:
        key = '{}_{}'.format(name, lang)

        def get_source_val(src, key):
            return src[key].replace('\u0000', ' ').replace('\\r', '\n')

        # Case 1: all translations missing from source
        if val is None:
            # Our API returns null as the value of a translated
            # field which has all languages missing.
            assert key not in src or len(get_source_val(src, key).split()) == 0
            return

        # Case 2: some or no translations missing from source
        s = None
        try:
            s = get_source_val(src, key)
        except KeyError:
            # Currently the API omits missing keys from the translated dict
            assert lang not in val
            return
        if len(s.split()) == 0:
            assert lang not in val
            return

        # compare ignoring whitespace and empty bytes
        assert s.split() == val[lang].split()


def assert_accessibility_viewpoints_match(src, dest):
    regenerated = []
    for key, val in dest.items():
        if val is None:
            val = 'unknown'
        regenerated.append('{}:{}'.format(key, val))
    assert ','.join(sorted(regenerated)) == src


def assert_unit_correctly_imported(unit, source_unit):
    d = unit
    s = source_unit

    #  1. required fields
    assert_field_match('id', s, d, required=True)

    # TODO: field is missing from importer and API
    # assert d['manual_coordinates'] == s['manual_coordinates']
    assert d['public'] == s['is_public']

    key = 'accessibility_viewpoints'
    assert_accessibility_viewpoints_match(s[key], d[key])

    # reference fields
    for sfield, dfield in [
            ('dept_id', 'department'),
            ('org_id', 'organization')]:
        assert str(d[dfield]) == s[sfield]

    for sfield, dfield in [
            ('ontologytree_ids', 'tree_nodes'),
            ('ontologyword_ids', 'ontologyword_ids')]:
        assert d[dfield] == s[sfield]

    #  2. optional fields
    for field_name in [
            'provider_type',
            'organizer_type']:
        if field_name in s:
            assert d[field_name] == s[field_name]
        else:
            assert d[field_name] is None

    for field_name in [
            'accessibility_email',
            'accessibility_phone',
            'picture_entrance_url',
            'picture_url',
            'streetview_entrance_url']:
        assert_string_field_match(field_name, s, d)

    for field_name in [
            'address_postal_full',
            'call_charge_info',
            'desc',
            'name',  # R
            'picture_caption',
            'short_desc',
            'street_address',
            'www']:
        assert_translated_field_match(field_name, s, d)

    if 'address_city_fi' in s and len(s['address_city_fi']) > 0:
        # TODO: improve API behavior
        assert d['municipality'] == s['address_city_fi'].lower()
    else:
        assert d['municipality'] is None

    # OK string
    # ======
    # OK 'accessibility_viewpoints' R
    # OK 'accessibility_www'
    # OK 'address_zip'
    # OK 'data_source_url'
    # OK 'email'
    # OK 'fax'
    # OK 'phone'
    # OK 'organizer_business_id'
    # OK 'source'

    # boolean
    # ===========
    # OK 'manual_coordinates' R
    # OK 'is_public" R

    # reference
    # ===========
    # 'dept_id' R
    # 'org_id' R
    # 'ontologytree_ids' R
    # 'ontologyword_ids' R
    # 'extra_searchwords' -> keywords

    # structured
    # ==========
    # 'sources' R

    # enum
    # ====
    # OK 'provider_type'
    # OK 'organizer_type'

    # datetimes
    # =========
    # 'modified_time'
    # 'created_time'

    # coordinates
    # ===========
    # 'easting_etrs_gk25'
    # 'easting_etrs_tm35fin'
    # 'northing_etrs_gk25'
    # 'northing_etrs_tm35fin'
    # 'latitude'
    # 'longitude'

    # url (maybe just string)
    # ===
    # OK 'picture_entrance_url'
    # OK 'picture_url'
    # OK 'streetview_entrance_url'


@pytest.mark.django_db
@given(lists(closed_object_set()))
@settings(max_examples=200, timeout=60)
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
