import pytest
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


@pytest.mark.parametrize("test_input,expected", [('page=1', [0, 1, 2, 3]),
                                                 ('page=1&page_size=3', [1, 2, 3]),
                                                 ('page=2&page_size=2', [0, 1])])
@pytest.mark.django_db
def test_page_filter(service_nodes_tree, api_client, test_input, expected):
    res = get_service_node_list(api_client, query_string=test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e


@pytest.mark.parametrize("test_input,expected", [('id', [None] * 4),
                                                 ('id,name', [{'fi': 'servicenode_0'}, {'fi': 'servicenode_1'},
                                                              {'fi': 'servicenode_2'}, {'fi': 'servicenode_3'}])])
@pytest.mark.django_db
def test_only_filter(service_nodes_tree, api_client, test_input, expected):
    res = get_service_node_list(api_client, query_string='only=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == res.index(r)
        assert r.get('name') == e


@pytest.mark.django_db
def test_include_filter(service_nodes_tree, services, api_client):
    res = get_service_node_list(api_client, query_string='include=related_services')
    assert len(res) == 4
    assert len(res[0]['related_services']) == 1
    assert res[0]['related_services'][0]['name'] == {'fi': 'service_0'}


@pytest.mark.parametrize("test_input,expected", [('0', [0]),
                                                 ('1,3', [1, 3]),
                                                 ('1,3,2', [1, 2, 3])])
@pytest.mark.django_db
def test_service_id_filter(services, api_client, test_input, expected):
    res = get_service_node_list(api_client, query_string='id=' + test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e
