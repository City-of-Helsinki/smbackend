import pytest
import datetime

from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from services.management.commands.services_import.services import update_service_node_counts
from services.models import ServiceNode, Unit, Department
from munigeo.models import AdministrativeDivisionType, AdministrativeDivision, Municipality
from .utils import get


MOD_TIME = datetime.datetime(year=2019, month=1, day=1, hour=1, minute=1, second=1)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def municipalities():
    t, created = AdministrativeDivisionType.objects.get_or_create(id=1, type='muni', defaults={'name': 'Municipality'})
    for i, muni_name in enumerate(['a', 'b']):
        a, created = AdministrativeDivision.objects.get_or_create(type=t, id=i, name_fi=muni_name)
        Municipality.objects.get_or_create(id=muni_name, name_fi=muni_name, division=a)
    return Municipality.objects.all().order_by('pk')


@pytest.fixture
def root_departments():
    m = municipalities()
    Department.objects.get_or_create(id='c', uuid='da792f32-6da7-4804-8059-16491b1ec0fa', name='c',
                                     municipality=m.get(id='a'))
    Department.objects.get_or_create(id='d', uuid='92f9182e-0942-4d82-8b6a-09499fe9c46a', name='d',
                                     municipality=m.get(id='b'))
    return Department.objects.all().order_by('pk')


@pytest.fixture
def service_nodes():
    ServiceNode.objects.get_or_create(id=1, name_fi='ServiceNode 1', last_modified_time=MOD_TIME)
    ServiceNode.objects.get_or_create(id=2, name_fi='ServiceNode 2', last_modified_time=MOD_TIME)
    ServiceNode.objects.get_or_create(id=3, name_fi='ServiceNode 3', last_modified_time=MOD_TIME)
    ServiceNode.objects.get_or_create(id=4, name_fi='ServiceNode 4', last_modified_time=MOD_TIME)
    return ServiceNode.objects.all().order_by('pk')


@pytest.fixture
def units(service_nodes, municipalities, root_departments):

    # |----+-----+-----+----+----+-----+-----|
    # |    | u1  | u2  | u3 | u4 | u5  | u6  |
    # |----+-----+-----+----+----+-----+-----|
    # | s1 | a,c | b,c |    |    | a,d |     |
    # | s2 | a,c |     | -,-|    |     |     |
    # | s3 |     |     |    |    | a,d |     |
    # | s4 |     |     |    |    |     | -,c |
    # |----+-----+-----+----+----+-----+-----|
    #                         a,c
    # u     = unit
    # s     = service_node
    # a,b,- = municipality
    # c,d,- = root_department
    # a = c
    # b = d

    a, b = municipalities

    c, d = root_departments

    u1, _ = Unit.objects.get_or_create(id=1, name_fi='a', municipality=a, root_department=c,
                                       last_modified_time=MOD_TIME)
    u2, _ = Unit.objects.get_or_create(id=2, name_fi='b', municipality=b, root_department=c,
                                       last_modified_time=MOD_TIME)
    u3, _ = Unit.objects.get_or_create(id=3, name_fi='c', municipality=None, root_department=None,
                                       last_modified_time=MOD_TIME)
    u4, _ = Unit.objects.get_or_create(id=4, name_fi='d', municipality=a, root_department=c,
                                       last_modified_time=MOD_TIME)
    u5, _ = Unit.objects.get_or_create(id=5, name_fi='e', municipality=a, root_department=d,
                                       last_modified_time=MOD_TIME)
    u6, _ = Unit.objects.get_or_create(id=6, name_fi='f', municipality=None, root_department=d,
                                       last_modified_time=MOD_TIME)

    s1, s2, s3, s4 = service_nodes

    u1.service_nodes.add(s1)
    u1.service_nodes.add(s2)
    u2.service_nodes.add(s1)
    u3.service_nodes.add(s2)
    u5.service_nodes.add(s1)
    u5.service_nodes.add(s3)
    u6.service_nodes.add(s4)

    return Unit.objects.all().order_by('pk')


def get_nodes(api_client):
    response = get(api_client, reverse('servicenode-list'))
    return response.data['results']


@pytest.mark.django_db
def test_service_node_counts_delete_units(units, api_client):
    import pdb; pdb.set_trace()
    for service_node in get_nodes(api_client):
        assert service_node['unit_count']['total'] == 0
        assert len(service_node['unit_count']['municipality']) == 0
        assert 'city_as_department' not in service_node['unit_count']
        #assert len(service_node['unit_count']['city_as_department']) == 0

    update_service_node_counts()

    def check_before_deletions():
        service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])

        service_node_1 = service_nodes[0]
        service_node_2 = service_nodes[1]
        service_node_3 = service_nodes[2]
        service_node_4 = service_nodes[3]

        assert service_node_1['id'] == 1
        assert service_node_2['id'] == 2
        assert service_node_1['unit_count']['total'] == 3
        assert service_node_1['unit_count']['municipality']['a'] == 2
        assert service_node_1['unit_count']['municipality']['b'] == 1
        assert service_node_1['unit_count']['city_as_department']['c'] == 3
        assert service_node_1['unit_count']['city_as_department']['d'] == 2
        assert len(service_node_1['unit_count']['municipality']) == 2
        assert len(service_node_1['unit_count']['city_as_department']) == 2

        assert service_node_2['unit_count']['total'] == 2
        assert service_node_2['unit_count']['municipality']['a'] == 1
        assert service_node_2['unit_count']['municipality']['_unknown'] == 1
        assert service_node_2['unit_count']['city_as_department']['c'] == 1
        assert service_node_2['unit_count']['city_as_department']['_unknown'] == 0
        assert len(service_node_2['unit_count']['municipality']) == 2
        assert len(service_node_2['unit_count']['city_as_department']) == 1

        assert service_node_3['unit_count']['total'] == 1
        assert service_node_3['unit_count']['municipality']['a'] == 1
        assert service_node_3['unit_count']['city_as_department']['c'] == 1
        assert service_node_3['unit_count']['city_as_department']['d'] == 1
        assert len(service_node_3['unit_count']['municipality']) == 1
        #??
        assert len(service_node_3['unit_count']['city_as_department']) == 2

        assert service_node_4['unit_count']['total'] == 1
        assert service_node_4['unit_count']['municipality']['_unknown'] == 1
        assert service_node_4['unit_count']['city_as_department']['c'] == 1
        assert len(service_node_4['unit_count']['municipality']) == 1
        assert len(service_node_4['unit_count']['city_as_department']) == 1

    check_before_deletions()

    u = Unit.objects.get(pk=4)
    assert u.service_nodes.count() == 0
    u.delete()

    # Deleting a Unit without services shouldn't affect the results
    check_before_deletions()

    # From service nodes 1 & 2 remove one unit with muni 'a' (delete unit)
    Unit.objects.get(pk=1).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]
    service_node_4 = service_nodes[3]

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 2
    assert service_node_1['unit_count']['municipality']['a'] == 1
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['c'] == 2
    assert service_node_1['unit_count']['city_as_department']['d'] == 2
    assert len(service_node_1['unit_count']['municipality']) == 2
    #??
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_2['unit_count']['total'] == 1
    assert service_node_2['unit_count']['municipality'].get('a') is None
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert service_node_2['unit_count']['city_as_department'].get('c') is None
    assert len(service_node_2['unit_count']['municipality']) == 1
    assert len(service_node_2['unit_count']['city_as_department']) == 0

    assert service_node_3['unit_count']['total'] == 1
    assert service_node_3['unit_count']['municipality']['a'] == 1
    assert service_node_3['unit_count']['city_as_department']['c'] == 1
    assert service_node_3['unit_count']['city_as_department']['d'] == 1
    assert len(service_node_3['unit_count']['municipality']) == 1
    #??
    assert len(service_node_3['unit_count']['city_as_department']) == 2

    assert service_node_4['unit_count']['total'] == 1
    assert service_node_4['unit_count']['municipality']['_unknown'] == 1
    assert service_node_4['unit_count']['city_as_department']['c'] == 1
    assert len(service_node_4['unit_count']['municipality']) == 1
    assert len(service_node_4['unit_count']['city_as_department']) == 1

    # From service node 3 remove all units (delete unit)
    Unit.objects.get(pk=5).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]
    service_node_4 = service_nodes[3]

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 1
    assert service_node_1['unit_count']['municipality'].get('a') is None
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['c'] == 1
    assert service_node_1['unit_count']['city_as_department']['d'] == 1
    assert len(service_node_1['unit_count']['municipality']) == 1
    #??
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_2['unit_count']['total'] == 1
    assert service_node_2['unit_count']['municipality'].get('a') is None
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert service_node_2['unit_count']['city_as_department'].get('c') is None
    assert len(service_node_2['unit_count']['municipality']) == 1
    assert len(service_node_2['unit_count']['city_as_department']) == 0

    assert service_node_3['unit_count']['total'] == 0
    assert len(service_node_3['unit_count']['municipality']) == 0
    assert len(service_node_3['unit_count']['city_as_department']) == 0

    assert service_node_4['unit_count']['total'] == 1
    assert service_node_4['unit_count']['municipality']['_unknown'] == 1
    assert service_node_4['unit_count']['city_as_department']['c'] == 1
    assert len(service_node_4['unit_count']['municipality']) == 1
    assert len(service_node_4['unit_count']['city_as_department']) == 1

    # From service node 2 remove unit with muncipality None
    Unit.objects.get(pk=3).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]
    service_node_4 = service_nodes[3]

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 1
    assert service_node_1['unit_count']['municipality'].get('a') is None
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['c'] == 1
    assert service_node_1['unit_count']['city_as_department']['d'] == 1
    assert len(service_node_1['unit_count']['municipality']) == 1
    # ??
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_2['unit_count']['total'] == 0
    assert service_node_2['unit_count']['municipality'].get('a') is None
    assert service_node_2['unit_count']['municipality'].get('_unknown') is None
    assert service_node_2['unit_count']['city_as_department'].get('c') is None
    assert len(service_node_2['unit_count']['municipality']) == 0
    assert len(service_node_2['unit_count']['city_as_department']) == 0

    assert service_node_3['unit_count']['total'] == 0
    assert len(service_node_3['unit_count']['municipality']) == 0
    assert len(service_node_3['unit_count']['city_as_department']) == 0

    assert service_node_4['unit_count']['total'] == 1
    assert service_node_4['unit_count']['municipality']['_unknown'] == 1
    assert service_node_4['unit_count']['city_as_department']['c'] == 1
    assert len(service_node_4['unit_count']['municipality']) == 1
    assert len(service_node_4['unit_count']['city_as_department']) == 1


@pytest.mark.django_db
def test_service_node_counts_add_service_node_to_units(units, api_client):
    # Add service node 3 to all units
    sn3_obj = ServiceNode.objects.get(pk=3)
    for o in Unit.objects.all():
        o.service_nodes.add(sn3_obj)

    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])
    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]
    service_node_4 = service_nodes[3]

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 3
    assert service_node_1['unit_count']['municipality']['a'] == 2
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['c'] == 3
    assert service_node_1['unit_count']['city_as_department']['d'] == 2
    assert len(service_node_1['unit_count']['municipality']) == 2
    assert len(service_node_1['unit_count']['city_as_department']) == 3

    assert service_node_2['unit_count']['total'] == 2
    assert service_node_2['unit_count']['municipality']['a'] == 1
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert service_node_2['unit_count']['city_as_department']['c'] == 1
    assert service_node_2['unit_count']['city_as_department']['_unknown'] == 0
    assert len(service_node_2['unit_count']['municipality']) == 2
    assert len(service_node_2['unit_count']['city_as_department']) == 1

    assert service_node_3['unit_count']['total'] == 6
    assert service_node_3['unit_count']['municipality']['a'] == 3
    assert service_node_3['unit_count']['municipality']['b'] == 1
    assert service_node_3['unit_count']['municipality']['_unknown'] == 2
    assert service_node_3['unit_count']['city_as_department']['c'] == 5
    assert service_node_3['unit_count']['city_as_department']['d'] == 2
    assert len(service_node_3['unit_count']['municipality']) == 3
    assert len(service_node_3['unit_count']['city_as_department']) == 2

    assert service_node_4['unit_count']['total'] == 1
    assert service_node_4['unit_count']['municipality']['_unknown'] == 1
    assert service_node_4['unit_count']['city_as_department']['c'] == 1
    assert len(service_node_4['unit_count']['municipality']) == 1
    assert len(service_node_4['unit_count']['city_as_department']) == 1


@pytest.mark.django_db
def test_service_node_counts_remove_service_node_from_units(units, api_client):
    # Remove service node 1 from all units
    sn1_obj = ServiceNode.objects.get(pk=1)
    for unit in sn1_obj.units.all():
        unit.service_nodes.remove(sn1_obj)

    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])
    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]
    service_node_4 = service_nodes[3]

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 0
    assert len(service_node_1['unit_count']['municipality']) == 0
    assert len(service_node_1['unit_count']['city_as_department']) == 0

    assert service_node_2['unit_count']['total'] == 2
    assert service_node_2['unit_count']['municipality']['a'] == 1
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert len(service_node_2['unit_count']['municipality']) == 2
    assert len(service_node_2['unit_count']['city_as_department']) == 1

    assert service_node_3['unit_count']['total'] == 1
    assert service_node_3['unit_count']['municipality']['a'] == 1
    assert len(service_node_3['unit_count']['municipality']) == 1
    assert len(service_node_3['unit_count']['city_as_department']) == 2

    assert service_node_4['unit_count']['total'] == 1
    assert service_node_4['unit_count']['municipality']['_unknown'] == 1
    assert service_node_4['unit_count']['city_as_department']['c'] == 1
    assert len(service_node_4['unit_count']['municipality']) == 1
    assert len(service_node_4['unit_count']['city_as_department']) == 1
