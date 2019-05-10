from uuid import UUID
import pytest
from rest_framework.reverse import reverse

from services.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;
from services.tests.endpoint_tests.fixtures import data
from services.tests.utils import get

deps = [UUID(uuid) for uuid in data['departments']]


def get_department_list(api_client, data=None, query_string=None):
    url = reverse('department-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data['results']
    res.sort(key=lambda r: deps.index(r['id']))
    return res


@pytest.mark.parametrize("test_input,expected", [('page=1', deps),
                                                 ('page=1&page_size=2', deps[:2]),
                                                 ('page=2&page_size=2', deps[2:])])
@pytest.mark.django_db
def test_page_filter(departments, api_client, test_input, expected):
    res = get_department_list(api_client, query_string=test_input)
    assert len(res) == len(expected)
    for r, e in zip(res, expected):
        assert r['id'] == e


@pytest.mark.parametrize("test_input,expected", [('id', [None] * 3),
                                                 ('id,name', [{'fi': 'dep_0'}, {'fi': 'dep_1'}, {'fi': 'dep_2'}])])
@pytest.mark.django_db
def test_only_filter(departments, api_client, test_input, expected):
    res = get_department_list(api_client, query_string='only=' + test_input)
    assert len(res) == len(expected)
    for r, d, e in zip(res, deps, expected):
        assert r['id'] == d
        assert r.get('name') == e


@pytest.mark.django_db
def test_include_filter(departments, api_client):
    res = get_department_list(api_client, query_string='include=municipality')
    assert len(res) == 3
    assert res[0]['municipality']['name'] == {'fi': 'muni_0'}
