import pytest  # noqa: F401;

from rest_framework.reverse import reverse

from services.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;
from services.tests.utils import get


def get_service_list(api_client, data=None, query_string=None):
    url = reverse('service-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data['results']
    res.sort(key=lambda r: r['id'])
    return res


@pytest.mark.django_db
def test_page_filter(services, api_client):
    res = get_service_list(api_client, query_string='page=1')
    assert len(res) == 4
    assert res[0]['id'] == 0
    assert res[3]['id'] == 3

    res = get_service_list(api_client, query_string='page=1&page_size=2')
    assert len(res) == 2
    assert res[0]['id'] == 2
    assert res[1]['id'] == 3

    res = get_service_list(api_client, query_string='page=2&page_size=2')
    assert len(res) == 2
    assert res[0]['id'] == 0
    assert res[1]['id'] == 1


@pytest.mark.django_db
def test_only_filter(services, api_client):
    res = get_service_list(api_client, query_string='only=id')
    assert len(res) == 4
    assert res[0]['id'] == 0
    assert res[0].get('name') is None


@pytest.mark.django_db
def test_only_filter_several_values(services, api_client):
    res = get_service_list(api_client, query_string='only=id,name')
    assert len(res) == 4
    assert res[0]['id'] == 0
    assert res[0]['name'] == {'fi': 'service_0'}


@pytest.mark.skip(reason="test not working, temporary disabled")
@pytest.mark.django_db
def test_include_filter(services, api_client):
    res = get_service_list(api_client, query_string='include=root_service_node')
    print(res)
    assert len(res) == 4
    assert res[0]['root_service_node']['name'] == 'service_node_0'


@pytest.mark.django_db
def test_service_id_filter(units, api_client):
    res = get_service_list(api_client, query_string='id=0')
    assert len(res) == 1
    assert res[0]['id'] == 0


@pytest.mark.django_db
def test_service_id_filter_several_values(units, api_client):
    ids = [0, 1]
    res = get_service_list(api_client, query_string='id={0},{1}'.format(ids[0], ids[1]))
    assert len(res) == 2
    for i in range(len(res)):
        assert res[i]['id'] == ids[i]
