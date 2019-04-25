from uuid import UUID
import pytest  # noqa: F401;

from rest_framework.reverse import reverse

from services.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;
from services.tests.utils import get
from services.models.unit import PROVIDER_TYPES
from smbackend.settings_test import LEVELS

pt = dict(PROVIDER_TYPES)


def get_unit_list(api_client, data=None, query_string=None):
    url = reverse('unit-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data['results']
    res.sort(key=lambda r: r['id'])
    return res


@pytest.mark.django_db
def test_unit_id_filter(units, api_client):
    res = get_unit_list(api_client, query_string='id=0')
    assert len(res) == 1
    assert res[0]['id'] == 0


@pytest.mark.django_db
def test_unit_id_filter_several_values(units, api_client):
    ids = [0, 1]
    res = get_unit_list(api_client, query_string='id={0},{1}'.format(ids[0], ids[1]))
    assert len(res) == 2
    for i in range(len(res)):
        assert res[i]['id'] == ids[i]


@pytest.mark.django_db
def test_municipality_filter(units, api_client):
    res = get_unit_list(api_client, query_string='municipality=muni_1')
    assert len(res) == 1
    assert res[0]['municipality'] == 'muni_1'


@pytest.mark.django_db
def test_municipality_filter_several_values(units, api_client):
    munis = ['muni_0', 'muni_1']
    res = get_unit_list(api_client, query_string='municipality={0},{1}'.format(munis[0], munis[1]))
    assert len(res) == 3
    assert res[0]['municipality'] == munis[0]
    assert res[1]['municipality'] == munis[1]
    assert res[2]['municipality'] == munis[0]


@pytest.mark.django_db
def test_city_as_department_filter(units, api_client):
    res = get_unit_list(api_client, query_string='city_as_department=92f9182e-0942-4d82-8b6a-09499fe9c46a')
    assert len(res) == 1
    assert res[0]['root_department'] == UUID('92f9182e-0942-4d82-8b6a-09499fe9c46a')
    assert res[0]['municipality'] == 'muni_1'


@pytest.mark.django_db
def test_city_as_department_filter_several_values(units, api_client):
    deps = ['da792f32-6da7-4804-8059-16491b1ec0fa', '92f9182e-0942-4d82-8b6a-09499fe9c46a']
    res = get_unit_list(api_client, query_string='city_as_department={0},{1}'.format(deps[0], deps[1]))
    assert len(res) == 3
    assert res[0]['root_department'] == UUID(deps[0])
    assert res[1]['root_department'] == UUID(deps[1])
    assert res[2]['root_department'] == UUID(deps[0])


@pytest.mark.skip(reason="test not working, temporary disabled")
@pytest.mark.django_db
def test_division_filter(units, api_client):
    res = get_unit_list(api_client, query_string='division=ocd-division/country:fi/kunta:muni_0')
    print('_____0', res)
    assert len(res) == 1
    assert res[0]['municipality'] == 'muni_0'


@pytest.mark.skip(reason="test not working, temporary disabled")
@pytest.mark.django_db
def test_division_filter_several_values(units, api_client):
    munis = ['muni_0', 'muni_1']
    res = get_unit_list(api_client, query_string='division=ocd-division/country:fi/kunta:{0},'
                                                 'ocd-division/country:fi/kunta:{1}'.format(munis[0], munis[1]))
    print('_____1', res)
    assert len(res) == 2
    for i in range(len(res)):
        assert res[i]['municipality'] == munis[i]


@pytest.mark.django_db
def test_provider_type_filter(units, api_client):
    res = get_unit_list(api_client, query_string='provider_type=1')
    assert len(res) == 1
    assert res[0]['provider_type'] == pt[1]


@pytest.mark.django_db
def test_provider_type_filter_several_values(units, api_client):
    types = [pt[1], pt[2]]
    res = get_unit_list(api_client, query_string='provider_type=1,2')
    assert len(res) == 2
    for i in range(len(res)):
        assert res[i]['provider_type'] == types[i]


@pytest.mark.django_db
def test_provider_type_not_filter(units, api_client):
    res = get_unit_list(api_client, query_string='provider_type__not=1')
    assert len(res) == 3
    for i in range(len(res)):
        assert res[0]['provider_type'] != pt[1]


@pytest.mark.django_db
def test_provider_type_not_filter_several_values(units, api_client):
    res = get_unit_list(api_client, query_string='provider_type__not=1,2,3')
    assert len(res) == 0


@pytest.mark.django_db
def test_service_filter(units, unit_service_details, api_client):
    res = get_unit_list(api_client, query_string='service=0')
    assert len(res) == 1
    assert res[0]['services'][0] == 0


@pytest.mark.django_db
def test_service_filter_several_values(units, unit_service_details, api_client):
    services = [0, 1]
    res = get_unit_list(api_client, query_string='service=0,1')
    assert len(res) == 2
    for i in range(len(res)):
        assert res[i]['services'][0] == services[i]

##############################################
# these not working because of service_node. ¿related to many to many relation?


# returns both units but should return only one
@pytest.mark.skip(reason="test not working, temporary disabled")
@pytest.mark.django_db
def test_level_filter(units, api_client):
    levels = list(LEVELS.keys())
    res = get_unit_list(api_client, query_string='level=' + levels[0])
    print('_____2', res)
    assert len(res) == 1
    assert len(res[0]['service_nodes']) == 1
    assert res[0]['service_nodes'][0] == 0


# returns both units but should return only one
@pytest.mark.skip(reason="test not working, temporary disabled")
@pytest.mark.django_db
def test_service_node_filter(units, api_client):
    res = get_unit_list(api_client, query_string='service_node=1')
    print('_____3', res)
    assert len(res) == 1
    assert len(res[0]['service_nodes']) == 1
    assert res[0]['service_nodes'][0] == 0


@pytest.mark.skip(reason="temporary disabled")
@pytest.mark.django_db
def test_category_filter_service_node(units, unit_service_details, api_client):
    res = get_unit_list(api_client, query_string='category=service_node:0')
    assert len(res) == 1
    assert res[0]['service_nodes'][0] == 0


@pytest.mark.skip(reason="test not working, temporary disabled")
@pytest.mark.django_db
def test_category_filter_several_values_service_node(units, unit_service_details, api_client):
    res = get_unit_list(api_client, query_string='category=service_node:0,service_node:1')
    assert len(res) == 2
    assert res[0]['service_nodes'][0] == 0
    assert res[1]['service_nodes'][0] == 1

    res = get_unit_list(api_client, query_string='category=service:0,service_node:1')
    assert len(res) == 2
    assert res[0]['services'][0] == 0
    assert res[1]['service_nodes'][0] == 1

##############################################


@pytest.mark.django_db
def test_category_filter_service(units, unit_service_details, api_client):
    res = get_unit_list(api_client, query_string='category=service:0')
    assert len(res) == 1
    assert res[0]['services'][0] == 0


@pytest.mark.django_db
def test_category_filter_service_several_values(units, unit_service_details, api_client):
    res = get_unit_list(api_client, query_string='category=service:0,service:1')
    assert len(res) == 2
    assert res[0]['services'][0] == 0
    assert res[1]['services'][0] == 1


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
