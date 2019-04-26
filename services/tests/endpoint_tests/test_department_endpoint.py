from uuid import UUID

import pytest  # noqa: F401;

from rest_framework.reverse import reverse

from services.tests.endpoint_tests.fixtures import *  # noqa: F403, F401;
from services.tests.utils import get

deps = [UUID('da792f32-6da7-4804-8059-16491b1ec0fa'), UUID('92f9182e-0942-4d82-8b6a-09499fe9c46a'),
        UUID('13108190-6157-4205-ad8e-1b92c084673a')]


def get_department_list(api_client, data=None, query_string=None):
    url = reverse('department-list')
    if query_string:
        url = '%s?%s' % (url, query_string)
        print(url)
    res = get(api_client, url, data=data).data['results']
    res.sort(key=lambda r: deps.index(r['id']))
    return res


@pytest.mark.django_db
def test_page_filter(departments, api_client):
    res = get_department_list(api_client, query_string='page=1')
    assert len(res) == 3
    assert res[0]['id'] == deps[0]
    assert res[2]['id'] == deps[2]

    res = get_department_list(api_client, query_string='page=1&page_size=2')
    assert len(res) == 2
    assert res[0]['id'] == deps[0]
    assert res[1]['id'] == deps[1]

    res = get_department_list(api_client, query_string='page=2&page_size=2')
    assert len(res) == 1
    assert res[0]['id'] == deps[2]


@pytest.mark.django_db
def test_only_filter(departments, api_client):
    res = get_department_list(api_client, query_string='only=id')
    assert len(res) == 3
    assert res[0]['id'] == deps[0]
    assert res[0].get('name') is None


@pytest.mark.django_db
def test_only_filter_several_values(departments, api_client):
    res = get_department_list(api_client, query_string='only=id,name')
    assert len(res) == 3
    assert res[1]['id'] == deps[1]
    assert res[1]['name'] == {'fi': 'dep_1'}


@pytest.mark.django_db
def test_include_filter(departments, api_client):
    res = get_department_list(api_client, query_string='include=municipality')
    assert len(res) == 3
    assert res[0]['municipality']['name'] == {'fi': 'muni_0'}
