from uuid import UUID

from rest_framework.reverse import reverse
from services.tests.endpoint_tests.fixtures import *
from services.tests.utils import get


def get_unit_list(api_client, data=None, query_string=None):
    url = reverse('unit-list')
    print(url)
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data)
    return res


@pytest.mark.django_db
def test_unit_id_filter(units, api_client):
    res = get_unit_list(api_client, query_string='id=0')
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['id'] == 0


@pytest.mark.django_db
def test_municipality_filter(units, api_client):
    res = get_unit_list(api_client, query_string='municipality=muni_0')
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['municipality'] == 'muni_0'


@pytest.mark.django_db
def test_city_as_department_filter(units, api_client):
    res = get_unit_list(api_client, query_string='city_as_department=da792f32-6da7-4804-8059-16491b1ec0fa')
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['root_department'] == UUID('da792f32-6da7-4804-8059-16491b1ec0fa')
    assert res.data['results'][0]['municipality'] == 'muni_0'
