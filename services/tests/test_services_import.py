from hypothesis import given

import pytest
import math

from django.conf import settings as django_settings

from rest_framework.test import APIClient
from rest_framework.reverse import reverse

# from services.management.commands.services_import.services import import_services
from services.management.commands.services_import.organizations import import_organizations
from services.management.commands.services_import.departments import import_departments
from services.management.commands.services_import.services import import_services
from services.management.commands.services_import.units import import_units

from services_import_hypothesis import closed_object_set


def get(api_client, url, data=None):
    response = api_client.get(url, data=data, format='json')
    assert response.status_code == 200, str(response.content)
    return response


@pytest.fixture
def api_client():
    return APIClient()

LANGUAGES = [l[0] for l in django_settings.LANGUAGES]

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
            ('ontologyword_ids', 'services')]:
        assert set(d[dfield]) == set(s[sfield]), sfield

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

    if 'latitude' in s:
        assert 'longitude' in s
        c = d['location']['coordinates']
        assert math.isclose(c[0], s['longitude'], rel_tol=1e-6)
        assert math.isclose(c[1], s['latitude'], rel_tol=1e-6)

    for lang in LANGUAGES:
        key = 'extra_searchwords_{}'.format(lang)
        if key not in s:
            assert lang not in d['keywords']
            continue
        exploded = set((e.strip() for e in s[key].split(',') if len(e.strip()) > 0))
        if len(exploded) == 0:
            continue
        result = d['keywords'][lang]
        assert len(exploded) == len(result)
        for kw in result:
            # raises an exception if kw doesn't match any item
            next(item for item in exploded if kw == item.strip())

    def map_source(source):
        return {'namespace': source['source'], 'value': source['id']}

    def source_found_in(id_list, source):
        return map_source(source) in id_list

    if 'sources' in s:
        for source in s['sources']:
            assert source_found_in(d['identifiers'], source)


    # TODO accessibility-variables !!! other many-to-many fields
    # OK unit counts in services !!!


    # url (maybe just string)
    # ===
    # OK 'picture_entrance_url'
    # OK 'picture_url'
    # OK 'streetview_entrance_url'


def assert_resource_synced(response, resource_name, resources):
    # The API-exposed resource count must exactly equal the original
    # import source resource count.
    assert response.data['count'] == len(resources[resource_name])

    def id_set(resources):
        return set((x['id'] for x in resources))

    result_resources = response.data['results']

    # The ids in source and result must exactly match
    assert (id_set(result_resources) ==
            id_set(resources[resource_name]))


@pytest.mark.django_db
@given(closed_object_set())
def test_import_units(api_client, resources):

    def fetch_resource(name):
        return resources.get(name, set())

    def fetch_units():
        return fetch_resource('unit')

    org_syncher = import_organizations(fetch_resource=fetch_resource)
    dept_syncher = import_departments(fetch_resource=fetch_resource)

    import_services(
        ontologytrees=fetch_resource('ontologytree'),
        ontologywords=fetch_resource('ontologyword'))

    response = get(api_client, reverse('ontologytreenode-list'))
    assert_resource_synced(response, 'ontologytree', resources)

    response = get(api_client, reverse('ontologyword-list'))
    assert_resource_synced(response, 'ontologyword', resources)

    import_units(
        fetch_units=fetch_units, fetch_resource=fetch_resource,
        org_syncher=org_syncher, dept_syncher=dept_syncher)

    response = get(api_client, reverse('unit-list'))
    assert_resource_synced(response, 'unit', resources)

    source_units_by_id = dict((u['id'], u) for u in resources['unit'])

    treenode_counts = {}
    ontologyword_counts = {}

    for unit in response.data['results']:
        assert_unit_correctly_imported(unit, source_units_by_id.get(unit['id']))
        for treenode_id in unit['tree_nodes']:
            treenode_counts[treenode_id] = treenode_counts.get(treenode_id, 0) + 1
        for ontologyword_id in unit['services']:
            ontologyword_counts[ontologyword_id] = ontologyword_counts.get(ontologyword_id, 0) + 1

    # Check unit counts in related objects

    response = get(api_client, reverse('ontologytreenode-list'))
    treenodes = response.data['results']
    for treenode in treenodes:
        assert treenode_counts.get(treenode['id'], 0) == treenode['unit_count']

    response = get(api_client, reverse('ontologyword-list'))
    ontologywords = response.data['results']
    for ontologyword in ontologywords:
        assert ontologyword_counts.get(ontologyword['id'], 0) == ontologyword['unit_count']
