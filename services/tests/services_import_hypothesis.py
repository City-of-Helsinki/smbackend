# from hypothesis import composite
from hypothesis import event
from hypothesis.strategies import (
    text, integers, booleans, lists, composite, uuids, sampled_from, none, one_of,
    floats, permutations, sets)
from string import digits, ascii_letters, punctuation

from django.conf import settings

SAFE_LETTERS = digits + ascii_letters + punctuation

LANGUAGES = [l[0] for l in settings.LANGUAGES]

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


def translated_field(draw, name, allow_missing=True, languages=LANGUAGES):
    result = {}
    for lang in languages:
        if allow_missing:
            val = draw(one_of(text(max_size=50), none()))
        else:
            val = draw(text(min_size=1, max_size=50))
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
    "UNKNOWN_PRODUCTION_METHOD",
    "VOUCHER_SERVICE"
]

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

ORGANIZATION_TYPES = [
    "MUNICIPALITY",
    "MUNICIPALLY_OWNED_COMPANY",
    "MUNICIPAL_ENTERPRISE_GROUP",
    "JOINT_MUNICIPAL_AUTHORITY",
    "OTHER_REGIONAL_COOPERATION_ORGANIZATION",
    "GOVERNMENT",
    "GOVERNMENTAL_COMPANY",
    "ORGANIZATION",
    "FOUNDATION",
    "ASSOCIATION",
    "PRIVATE_ENTERPRISE",
    "UNKNOWN"
]


@composite
def make_source(draw):
    return {'id': draw(text(SAFE_LETTERS, min_size=1, max_size=100)),
            'source': draw(text(SAFE_LETTERS, min_size=1, max_size=50))}


# TODO: add department organization type, then add tests for correct mapping

def add_extra_searchwords(draw, result):
    for lang in LANGUAGES:
        words = draw(sets(text(SAFE_LETTERS + 'åäöÅÄÖ ',
                               min_size=1, max_size=25)))
        if len(words) == 0:
            event('extra searchwords length {}'.format(len(words)))
            words = None
        else:
            event('extra searchwords length >0')
            words = ', '.join((word.strip() for word in words))
            result['extra_searchwords_{}'.format(lang)] = words


def unit_maker(draw, resource_ids):
    def make_unit(uid):
        # Required fields
        result = {
            'id': uid,
            'accessibility_viewpoints': accessibility_viewpoints(draw),
            'dept_id': str(draw(sampled_from(resource_ids['department']))),
            'org_id': str(draw(sampled_from(resource_ids['organization']))),
            'ontologytree_ids': draw(permutations(resource_ids['ontologytree'])),
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
            add_optional_field(name, text(max_size=50))

        add_optional_field('address_city', sampled_from(MUNICIPALITIES))
        add_optional_field('address_zip', text(max_size=10))
        add_optional_field('organizer_business_id', text(max_size=10))
        add_optional_field('organizer_name', text(max_size=10))

        for field in ['accessibility_email',
                      'accessibility_www',
                      'email',
                      'fax',
                      'phone',
                      'picture_entrance_url',
                      'picture_url',
                      'streetview_entrance_url']:
            add_optional_text_field(field)
        add_optional_field('data_source_url', text(max_size=30))

        result.update(translated_field(draw, 'address_postal_full', allow_missing=True))
        result.update(translated_field(draw, 'call_charge_info', allow_missing=True))
        result.update(translated_field(draw, 'desc', allow_missing=True))
        result.update(translated_field(draw, 'picture_caption', allow_missing=True))

        # Extra searchwords

        add_extra_searchwords(draw, result)

        add_optional_field('sources',
                           lists(make_source(), min_size=1, max_size=2))

        has_coordinates = draw(booleans())
        if has_coordinates:
            result['longitude'] = draw(floats(min_value=24, max_value=26))
            result['latitude'] = draw(floats(min_value=58, max_value=62))

        return result

    return make_unit


def organization_maker(*args):
    return lambda x: {'id': str(x)}


def department_maker(draw, resource_ids):
    def make_department(did):
        return {
            'id': str(did),
            'hierarchy_level': 0,
            'organization_type': draw(sampled_from(ORGANIZATION_TYPES)),
            'org_id': str(draw(sampled_from(resource_ids['organization'])))
        }
    return make_department


def ontologyword_maker(draw, *args):
    def make_ontologyword(x):
        result = {'id': x,
                  'can_add_schoolyear': draw(booleans()),
                  'can_add_clarification': draw(booleans())}
        add_extra_searchwords(draw, result)
        return result
    return make_ontologyword


def ontologytree_maker(draw, *args):
    def make_ontologytree(x):
        result = {'id': x}
        add_extra_searchwords(draw, result)
        return result
    return make_ontologytree


make_resource = {}
for r in RESOURCES:
    make_resource[r] = locals()['{}_maker'.format(r)]


def make_ontologyword_details(draw, unit_id, ontologyword_id):
    result = {
        'unit_id': unit_id,
        'ontologyword_id': ontologyword_id
    }
    if draw(booleans()):
        result['schoolyear'] = '2017-2018'  # TODO
    if draw(booleans()):
        result.update(translated_field(draw, 'clarification', allow_missing=False))
    return result


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

    resources['ontologyword_details'] = []
    for unit in resources['unit']:
        for oid in draw(permutations(ids['ontologyword'])):
            resources['ontologyword_details'].append(make_ontologyword_details(draw, unit['id'], oid))
    return resources
