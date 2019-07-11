from uuid import UUID

import pytest
from rest_framework.reverse import reverse

from services.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;
from services.tests.endpoint_tests.fixtures import data
from services.tests.utils import get
from services.models.unit import PROVIDER_TYPES
from smbackend.settings_test import LEVELS

pt = dict(PROVIDER_TYPES)
levels = list(LEVELS.keys())
deps = [UUID(uuid) for uuid in data['departments']]


def get_unit_list(api_client, data=None, query_string=None):
    url = reverse('unit-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data['results']
    res.sort(key=lambda r: r['id'])
    return res


@pytest.mark.parametrize("test_input,expected", [('page=1', [0, 1, 2, 3]),
                                                 ('page=1&page_size=3', [1, 2, 3]),
                                                 ('page=2&page_size=2', [0, 1])])
@pytest.mark.django_db
def test_page_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string=test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e


@pytest.mark.parametrize("test_input,expected", [('id', [None] * 4),
                                                 ('id,name', [{'fi': 'unit_0'}, {'fi': 'unit_1'},
                                                              {'fi': 'unit_2'}, {'fi': 'unit_3'}])])
@pytest.mark.django_db
def test_only_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='only=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == res.index(r)
        assert r.get('name') == e


@pytest.mark.django_db
def test_include_filter(units, api_client):
    res = get_unit_list(api_client, query_string='include=municipality')
    assert len(res) == 4
    assert res[0]['municipality']['name'] == {'fi': 'muni_0'}

    res = get_unit_list(api_client, query_string='include=municipality,root_department')
    assert len(res) == 4
    assert res[0]['municipality']['name'] == {'fi': 'muni_0'}
    assert res[0]['root_department']['name'] == {'fi': 'dep_0'}


@pytest.mark.parametrize("test_input,expected", [('0', [0]),
                                                 ('1,3', [1, 3]),
                                                 ('1,3,2', [1, 2, 3])])
@pytest.mark.django_db
def test_service_id_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='id=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e


@pytest.mark.parametrize("test_input,expected", [('muni_1', ['muni_1']),
                                                 ('muni_1,muni_2', ['muni_1', 'muni_2']),
                                                 ('muni_0,muni_2', ['muni_0', 'muni_2', 'muni_0'])])
@pytest.mark.django_db
def test_municipality_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='municipality=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['municipality'] == e


@pytest.mark.parametrize("test_input,expected", [(str(deps[2]), [[deps[2]], ['muni_2']]),
                                                 (str(deps[1]), [[deps[1]] * 2, ['muni_1', 'muni_0']]),
                                                 (str(deps[0]) + ',' + str(deps[1]),
                                                  [[deps[0], deps[1], deps[1]], ['muni_0', 'muni_1', 'muni_0']])])
@pytest.mark.django_db
def test_city_as_department_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='city_as_department=' + test_input)
    assert len(res) == len(expected[0])
    for r, e_d, e_m in zip(res, expected[0], expected[1]):
        assert r['root_department'] == e_d
        assert r['municipality'] == e_m


div_text = 'ocd-division/country:fi/kunta:muni_'


@pytest.mark.parametrize("test_input,expected", [(div_text + '0', [[0, 3], ['muni_0', 'muni_0']]),
                                                 (div_text + '1,' + div_text + '2', [[1, 2], ['muni_1', 'muni_2']]),
                                                 (div_text + '0,' + div_text + '1,' + div_text + '2',
                                                  [[0, 1, 2, 3], ['muni_0', 'muni_1', 'muni_2', 'muni_0']])])
@pytest.mark.django_db
def test_division_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='division=' + test_input)
    assert len(res) == len(expected[0])
    for r, e_id, e_m in zip(res, expected[0], expected[1]):
        assert r['id'] == e_id
        assert r['municipality'] == e_m


@pytest.mark.parametrize("test_input,expected", [('2', [1]),
                                                 ('3', [2, 3]),
                                                 ('1,3', [0, 2, 3]),
                                                 ('1,2,3', [0, 1, 2, 3])])
@pytest.mark.django_db
def test_provider_type_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='provider_type=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e


@pytest.mark.parametrize("test_input,expected", [('1', [1, 2, 3]),
                                                 ('3', [0, 1]),
                                                 ('1,2,3', [])])
@pytest.mark.django_db
def test_provider_type_not_filter(units, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='provider_type__not=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e


@pytest.mark.parametrize("test_input,expected", [('0', [[0], [[0]]]),
                                                 ('0,1', [[0, 1], [[0], [1]]]),
                                                 ('2,3', [[2], [[3, 2]]]),
                                                 ('0,2,3', [[0, 2], [[0], [3, 2]]])])
@pytest.mark.django_db
def test_service_filter(units, unit_service_details, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='service=' + test_input)
    assert len(res) == len(expected[0])
    for r, e_id, e_s in zip(res, expected[0], expected[1]):
        assert r['id'] == e_id
        assert r['services'] == e_s


@pytest.mark.parametrize("test_input,expected", [('0', [[0, 1, 2], [[0], [1], [2]]]),
                                                 ('1', [[1, 2], [[1], [2]]]),
                                                 ('2,3', [[2, 3], [[2], [3]]]),
                                                 ('0,3', [[0, 1, 2, 3], [[0], [1], [2], [3]]])])
@pytest.mark.django_db
def test_service_node_tree_filter(units, units_service_nodes_tree, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='service_node=' + test_input)
    assert len(res) == len(expected[0])
    for r, e_id, e_sn in zip(res, expected[0], expected[1]):
        assert r['id'] == e_id
        assert r['service_nodes'] == e_sn


@pytest.mark.parametrize("test_input,expected", [('0', [[0]]),
                                                 ('1,3', [[1], [3]]),
                                                 ('0, 1, 2, 3', [[0], [1], [2], [3]])])
@pytest.mark.django_db
def test_service_node_flat_filter(units, units_service_nodes_flat, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='service_node=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e[0]
        assert r['service_nodes'] == e


@pytest.mark.parametrize("test_input,expected", [(levels[0], [[0]]),
                                                 (levels[1], [[0], [1], [2]])])
@pytest.mark.django_db
def test_level_service_nodes_flat_filter(units, units_service_nodes_flat, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='level=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e[0]
        assert r['service_nodes'] == e


@pytest.mark.parametrize("test_input,expected", [(levels[0], [[0], [1], [2]]),
                                                 (levels[1], [[0], [1], [2]])])
@pytest.mark.django_db
def test_level_service_nodes_tree_filter(units, units_service_nodes_tree, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='level=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e[0]
        assert r['service_nodes'] == e


@pytest.mark.parametrize("test_input,expected", [('service:0', [[[0]], [0]]),
                                                 ('service:0,service:1', [[[0], [1]], [0, 1]]),
                                                 ('service_node:0', [[[0], [1], [3, 2]], [0, 1, 2]]),
                                                 ('service_node:0,service_node:1', [[[0], [1], [3, 2]], [0, 1, 2]]),
                                                 ('service:0,service_node:1,service_node:3',
                                                  [[[0], [1], [3, 2], []], [0, 1, 2, 3]]),
                                                 ('service:2,service:3', [[[3, 2]], [2]]),
                                                 ('service:2,service:3,service_node:3', [[[3, 2], []], [2, 3]])])
@pytest.mark.django_db
def test_category_filter(units, unit_service_details, units_service_nodes_tree, api_client, test_input, expected):
    res = get_unit_list(api_client, query_string='category=' + test_input)
    assert len(res) == len(expected[0])
    for r, s, s_n in zip(res, expected[0], expected[1]):
        assert r['id'] == s_n
        assert r['service_nodes'][0] == s_n
        assert r['services'] == s


@pytest.mark.django_db
def test_bbox_and_srid_filter(units, api_client):
    res = get_unit_list(api_client, query_string='bbox=385991.000,6672778.500,386659.000,6673421.500&srid=3067')
    assert len(res) == 2
    assert res[0]['name']['fi'] == 'unit_0'
    assert res[1]['name']['fi'] == 'unit_3'


@pytest.mark.django_db
def test_lat_lon_distance_filter(units, api_client):
    res = get_unit_list(api_client, query_string='lat=60.180459083&lon=24.952835651&distance=250')
    assert len(res) == 1
    assert res[0]['name']['fi'] == 'unit_3'

    res = get_unit_list(api_client, query_string='lat=60.180459083&lon=24.952835651&distance=350')
    assert len(res) == 2
    assert res[0]['name']['fi'] == 'unit_0'
    assert res[1]['name']['fi'] == 'unit_3'
