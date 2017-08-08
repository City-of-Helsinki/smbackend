# from hypothesis import composite
from hypothesis import event
from hypothesis.strategies import (
    text, integers, booleans, lists, composite, uuids, sampled_from, none, one_of,
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
        integers(min_value=1, max_value=15),
        min_size=1, max_size=3, unique=True))


def uuid_keys(draw):
    return draw(lists(uuids(), min_size=2, max_size=3))


def translated_field(draw, name, allow_missing=True, languages=['fi', 'sv', 'en']):
    result = {}
    for lang in languages:
        if allow_missing:
            val = draw(one_of(text(), none()))
        else:
            val = draw(text(min_size=1))
        if val is not None:
            result['{}_{}'.format(name, lang)] = val
    return result


VIEWPOINTS = ['00', '11', '12', '13', '21', '22', '23', '31', '32', '33', '41',
              '51', '52', '61']

VIEWPOINT_STATES = ['green', 'red', 'unknown']

MUNICIPALITIES = [  # TODO: read from independent source
    {
        'fi': 'Helsinki',
        'sv': 'Helsingfors',
        'en': 'Helsinki'
    },
    {
        'fi': 'Espoo',
        'sv': 'Esbo',
        'en': 'Espoo'
    },
    {
        'fi': 'Kauniainen',
        'sv': 'Grankulla',
        'en': 'Kauniainen'
    },
    {
        'fi': 'Vantaa',
        'sv': 'Vanda',
        'en': 'Vantaa'
    }
]


def accessibility_viewpoints(draw):
    return ','.join([
        '{}:{}'.format(key, draw(sampled_from(VIEWPOINT_STATES))) for key in VIEWPOINTS])


PROVIDER_TYPES = [
    "CONTRACT_SCHOOL",
    "OTHER_PRODUCTION_METHOD",
    "PAYMENT_COMMITMENT",
    "PURCHASED_SERVICE",
    "SELF_PRODUCED",
    "SUPPORTED_OPERATIONS",
    "UNKNOWN_PRODUCTION_METHOD"]

ORGANIZER_TYPES = [
    "ASSOCIATION",
    "FOUNDATION",
    "GOVERNMENT",
    "GOVERNMENTAL_COMPANY",
    "JOINT_MUNICIPAL_AUTHORITY",
    "MUNICIPAL_ENTERPRISE_GROUP",
    "MUNICIPALITY",
    "MUNICIPALLY_OWNED_COMPANY",
    "ORGANIZATION",
    "OTHER_REGIONAL_COOPERATION_ORGANIZATION",
    "PRIVATE_ENTERPRISE",
    "UNKNOWN"
]


@composite
def make_source(draw):
    return {'id': draw(text()), 'source': draw(text())}


def unit_maker(draw, resource_ids):
    def make_unit(uid):
        # Required fields
        result = {
            'id': uid,
            'accessibility_viewpoints': accessibility_viewpoints(draw),
            'dept_id': str(draw(sampled_from(resource_ids['department']))),
            'org_id': str(draw(sampled_from(resource_ids['organization']))),
            'ontologyword_ids': draw(permutations(resource_ids['ontologyword'])),
            'ontologytree_ids': draw(permutations(resource_ids['ontologytree'])),
            'sources': draw(lists(make_source(), min_size=0, max_size=2)),
            'provider_type': draw(sampled_from(PROVIDER_TYPES)),
            'organizer_type': draw(sampled_from(ORGANIZER_TYPES)),
            'manual_coordinates': draw(booleans()),
            # TODO: cannot test is_public=False until there is a mechanism
            # for getting non-public units from the API.
            'is_public': True,
            # TODO: map to another field
        }
        result.update(translated_field(draw, 'name', allow_missing=False))

        def add_optional_field(name, strategy):
            val = draw(one_of(none(), strategy))
            if val is not None:
                event('unit.{}: optional field given value'.format(name))
                result[name] = val
            else:
                event('unit.{}: optional field missing'.format(name))

        def add_optional_text_field(name):
            add_optional_field(name, text())

        add_optional_field('address_city', sampled_from(MUNICIPALITIES))
        add_optional_field('address_zip', text(max_size=10))
        add_optional_field('organizer_business_id', text(max_size=10))

        for field in ['accessibility_email',
                      'accessibility_www',
                      'data_source_url',
                      'email',
                      'fax',
                      'phone',
                      'source',
                      'picture_entrance_url',
                      'picture_url',
                      'streetview_entrance_url']:
            add_optional_text_field(field)

        result.update(translated_field(draw, 'address_postal_full', allow_missing=True))
        result.update(translated_field(draw, 'call_charge_info', allow_missing=True))
        result.update(translated_field(draw, 'desc', allow_missing=True))
        result.update(translated_field(draw, 'picture_caption', allow_missing=True))

        for lang in LANGUAGES:
            words = draw(sets(text(digits + ascii_letters + punctuation + 'åäöÅÄÖ ',
                                   min_size=1, max_size=25)))
            if len(words) == 0:
                event('extra searchwords empty')
                words = None
            else:
                words = ', '.join(words)
                result['extra_searchwords_{}'.format(lang)] = words
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
