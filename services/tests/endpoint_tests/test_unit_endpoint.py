from uuid import UUID

from rest_framework.reverse import reverse
from services.tests.endpoint_tests.fixtures import *
from services.tests.utils import get


def get_unit_list(api_client, data=None, query_string=None):
    url = reverse('unit-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data)
    return res


@pytest.mark.django_db
def test_unit_id_filter_one_value(units, api_client):
    res = get_unit_list(api_client, query_string='id=0')
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['id'] == 0


@pytest.mark.django_db
def test_unit_id_filter_several_values(units, api_client):
    res = get_unit_list(api_client, query_string='id=0,1')
    assert len(res.data['results']) == 2
    ids = [0, 1]
    for i in range(2):
        try:
            assert res.data['results'][i]['id'] == ids[0]
            ids.pop(0)
        except:
            assert res.data['results'][i]['id'] == ids[1]
            ids.pop(1)


@pytest.mark.django_db
def test_municipality_filter(units, api_client):
    res = get_unit_list(api_client, query_string='municipality=muni_0')
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['municipality'] == 'muni_0'


@pytest.mark.django_db
def test_municipality_filter_several_values(units, api_client):
    munis = ['muni_0', 'muni_1']
    res = get_unit_list(api_client, query_string='municipality={},{}'.format(munis[0], munis[1]))
    assert len(res.data['results']) == 2
    for i in range(2):
        try:
            assert res.data['results'][i]['municipality'] == munis[0]
            munis.pop(0)
        except:
            assert res.data['results'][i]['municipality'] == munis[1]
            munis.pop(1)


@pytest.mark.django_db
def test_city_as_department_filter(units, api_client):
    res = get_unit_list(api_client, query_string='city_as_department=da792f32-6da7-4804-8059-16491b1ec0fa')
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['root_department'] == UUID('da792f32-6da7-4804-8059-16491b1ec0fa')
    assert res.data['results'][0]['municipality'] == 'muni_0'


@pytest.mark.django_db
def test_city_as_department_filter_several_values(units, api_client):
    deps = ['da792f32-6da7-4804-8059-16491b1ec0fa', '92f9182e-0942-4d82-8b6a-09499fe9c46a']
    res = get_unit_list(api_client, query_string='city_as_department={0},{1}'.format(deps[0], deps[1]))
    assert len(res.data['results']) == 2
    for i in range(2):
        try:
            assert res.data['results'][i]['root_department'] == UUID(deps[0])
            deps.pop(0)
        except:
            assert res.data['results'][i]['root_department'] == UUID(deps[1])
            deps.pop(1)
