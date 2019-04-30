import pytest  # noqa: F401;

from rest_framework.reverse import reverse

from services.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;
from services.tests.utils import get


def get_service_node_list(api_client, data=None, query_string=None):
    url = reverse('servicenode-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data['results']
    res.sort(key=lambda r: r['id'])
    return res


@pytest.mark.django_db
def test_page_filter(service_nodes_tree, api_client):
    res = get_service_node_list(api_client, query_string='page=1')
    assert len(res) == 4
    assert res[0]['id'] == 0
    assert res[3]['id'] == 3

    res = get_service_node_list(api_client, query_string='page=1&page_size=2')
    assert len(res) == 2
    assert res[0]['id'] == 2
    assert res[1]['id'] == 3

    res = get_service_node_list(api_client, query_string='page=2&page_size=2')
    assert len(res) == 2
    assert res[0]['id'] == 0
    assert res[1]['id'] == 1


@pytest.mark.django_db
def test_only_filter(service_nodes_tree, api_client):
    res = get_service_node_list(api_client, query_string='only=id')
    assert len(res) == 4
    assert res[0]['id'] == 0
    assert res[0].get('name') is None

    res = get_service_node_list(api_client, query_string='only=id,name')
    assert len(res) == 4
    assert res[0]['id'] == 0
    assert res[0]['name'] == {'fi': 'servicenode_0'}


@pytest.mark.django_db
def test_include_filter(service_nodes_tree, services, api_client):
    res = get_service_node_list(api_client, query_string='include=related_services')
    assert len(res) == 4
    assert len(res[0]['related_services']) == 1
    assert res[0]['related_services'][0]['name'] == {'fi': 'service_0'}


@pytest.mark.django_db
def test_service_node_id_filter(service_nodes_tree, api_client):
    res = get_service_node_list(api_client, query_string='id=0')
    assert len(res) == 1
    assert res[0]['id'] == 0

    res = get_service_node_list(api_client, query_string='id=3')
    assert len(res) == 1
    assert res[0]['id'] == 3

    res = get_service_node_list(api_client, query_string='id=0,1')
    assert len(res) == 2
    assert res[0]['id'] == 0
    assert res[1]['id'] == 1
