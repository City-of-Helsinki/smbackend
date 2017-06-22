# from hypothesis import composite
from hypothesis import given
from hypothesis.strategies import (
    text, integers, lists, composite, uuids, sampled_from, none, one_of,
    permutations)

RESOURCES = [
    'unit',
    'organization',
    'department',
    'ontologyword',
    'ontologytree',
]


def int_keys(draw):
    return draw(lists(
        integers(min_value=1, max_value=1000000),
        min_size=1, max_size=3, unique=True))


def uuid_keys(draw):
    return draw(lists(uuids(), min_size=2, max_size=3))


def translated_field(draw, name, allow_none=True, languages=['fi', 'sv', 'en']):
    result = {}
    for lang in languages:
        if allow_none:
            val = draw(one_of(text(), none()))
        else:
            val = draw(text())
        result['name_{}'.format(lang)] = val
    return result


VIEWPOINTS = ['00', '11', '12', '13', '21', '22', '23', '31', '32', '33', '41',
              '51', '52', '61']

VIEWPOINT_STATES = ['green', 'red', 'unknown']


def accessibility_viewpoints(draw):
    return ','.join([
        '{}:{}'.format(key, draw(sampled_from(VIEWPOINT_STATES))) for key in VIEWPOINTS])


PROVIDER_TYPES = ["CONTRACT_SCHOOL",
                  "OTHER_PRODUCTION_METHOD",
                  "PAYMENT_COMMITMENT",
                  "PURCHASED_SERVICE",
                  "SELF_PRODUCED",
                  "SUPPORTED_OPERATIONS",
                  "UNKNOWN_PRODUCTION_METHOD"]


@composite
def make_source(draw):
    return {'id': draw(text()), 'source': draw(text())}


def unit_maker(draw, resource_ids):
    def make_unit(uid):
        result = {
            'id': uid,
            'org_id': str(draw(sampled_from(resource_ids['organization']))),
            'dept_id': str(draw(sampled_from(resource_ids['department']))),
            'ontologyword_ids': draw(permutations(resource_ids['ontologyword'])),
            'ontologytree_ids': draw(permutations(resource_ids['ontologytree'])),
            'accessibility_viewpoints': accessibility_viewpoints(draw),
            'sources': draw(lists(make_source(), min_size=0, max_size=2)),
            'provider_type': draw(sampled_from(PROVIDER_TYPES)),
            'accessibility_email': draw(one_of(text(), none()))  # TODO: map elsewhere?
        }
        result.update(translated_field(draw, 'name', allow_none=False))
        return result
    return make_unit


def organization_maker(*args):
    return lambda x: {'id': str(x)}


def department_maker(draw, resource_ids):
    def make_department(did):
        return {
            'id': str(did),
            'hierarchy_level': 0,
            'org_id': str(draw(sampled_from(resource_ids['organization'])))
        }
    return make_department


def ontologyword_maker(*args):
    return lambda x: {'id': x}


def ontologytree_maker(*args):
    return lambda x: {'id': x}


make_resource = {}
for r in RESOURCES:
    make_resource[r] = locals()['{}_maker'.format(r)]


@composite
def closed_object_set(draw):
    ids = {
        'unit': int_keys(draw),
        'organization': uuid_keys(draw),
        'department': uuid_keys(draw),
        'ontologyword': int_keys(draw),
        'ontologytree': int_keys(draw)
    }
    resources = {}
    for key, identifiers in ids.items():
        resources[key] = list(map(make_resource[key](draw, ids), ids[key]))
    return resources


@given(closed_object_set())
def test_something(cos):
    assert True
