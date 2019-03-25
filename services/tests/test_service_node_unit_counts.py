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
    for i, muni_name in enumerate(['a', 'b', 'c']):
        a, created = AdministrativeDivision.objects.get_or_create(type=t, id=i, name_fi=muni_name)
        Municipality.objects.get_or_create(id=muni_name, name_fi=muni_name, division=a)
    return Municipality.objects.all().order_by('pk')


@pytest.fixture
def root_departments(municipalities):
    a, b, c = municipalities

    Department.objects.get_or_create(uuid='da792f32-6da7-4804-8059-16491b1ec0fa', name='d',
                                     municipality=a)
    Department.objects.get_or_create(uuid='92f9182e-0942-4d82-8b6a-09499fe9c46a', name='e',
                                     municipality=b)
    Department.objects.get_or_create(uuid='36e20c18-4c9a-11e9-8646-d663bd873d93', name='f',
                                     municipality=c)
    return Department.objects.all().order_by('pk')


@pytest.fixture
def service_nodes():
    ServiceNode.objects.get_or_create(id=1, name_fi='ServiceNode 1', last_modified_time=MOD_TIME)
    ServiceNode.objects.get_or_create(id=2, name_fi='ServiceNode 2', last_modified_time=MOD_TIME)
    ServiceNode.objects.get_or_create(id=3, name_fi='ServiceNode 3', last_modified_time=MOD_TIME)
    return ServiceNode.objects.all().order_by('pk')


@pytest.fixture
def units(service_nodes, municipalities, root_departments):

    # |----+-----+-----+----+----+-----+
    # |    | u1  | u2  | u3 | u4 | u5  | u6
    # |----+-----+-----+----+----+-----+
    # | s1 | a,d | b,d |    |    | a,e |
    # | s2 | a,d |     | -,d|    |     |
    # | s3 |     |     |    |    | a,e | c,f
    # |----+-----+-----+----+----+-----|
    #                         a,d
    #
    # u     = unit
    # s     = service_node
    # a,b,c,- = municipality
    # d,e,f = root_department
    # a = d = da792f32-6da7-4804-8059-16491b1ec0fa
    # b = e = 92f9182e-0942-4d82-8b6a-09499fe9c46a
    # c = f
    #

    a, b, c = municipalities
    d, e, f = root_departments

    u1, _ = Unit.objects.get_or_create(id=1, name_fi='a', municipality=a, root_department=d,
                                       last_modified_time=MOD_TIME)
    u2, _ = Unit.objects.get_or_create(id=2, name_fi='b', municipality=b, root_department=d,
                                       last_modified_time=MOD_TIME)
    u3, _ = Unit.objects.get_or_create(id=3, name_fi='c', municipality=None, root_department=d,
                                       last_modified_time=MOD_TIME)
    u4, _ = Unit.objects.get_or_create(id=4, name_fi='d', municipality=a, root_department=d,
                                       last_modified_time=MOD_TIME)
    u5, _ = Unit.objects.get_or_create(id=5, name_fi='e', municipality=a, root_department=e,
                                       last_modified_time=MOD_TIME)
    u6, _ = Unit.objects.get_or_create(id=6, name_fi='f', municipality=c, root_department=f,
                                       last_modified_time=MOD_TIME)

    s1, s2, s3 = service_nodes

    u1.service_nodes.add(s1)
    u1.service_nodes.add(s2)
    u2.service_nodes.add(s1)
    u3.service_nodes.add(s2)
    u5.service_nodes.add(s1)
    u5.service_nodes.add(s3)
    u6.service_nodes.add(s3)
    # u4.service_nodes.add(s4)

    return Unit.objects.all().order_by('pk')


def get_nodes(api_client):
    response = get(api_client, reverse('servicenode-list'))
    return response.data['results']


@pytest.mark.django_db
def test_service_node_counts_delete_units(units, api_client):

    for service_node in get_nodes(api_client):
        assert service_node['unit_count']['total'] == 0
        assert len(service_node['unit_count']['municipality']) == 0
        assert len(service_node['unit_count']['city_as_department']) == 0

    update_service_node_counts()

    def check_before_deletions():
        service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])

        service_node_1 = service_nodes[0]
        service_node_2 = service_nodes[1]
        service_node_3 = service_nodes[2]

        assert service_node_1['id'] == 1
        assert service_node_2['id'] == 2
        assert service_node_1['unit_count']['total'] == 3
        assert service_node_1['unit_count']['municipality']['a'] == 2
        assert service_node_1['unit_count']['municipality']['b'] == 1
        assert service_node_1['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 3
        assert service_node_1['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 2
        assert len(service_node_1['unit_count']['municipality']) == 2
        assert len(service_node_1['unit_count']['city_as_department']) == 2

        assert service_node_2['unit_count']['total'] == 2
        assert service_node_2['unit_count']['municipality']['a'] == 1
        assert service_node_2['unit_count']['municipality']['_unknown'] == 1
        assert service_node_2['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 2
        assert service_node_2['unit_count']['city_as_department'].get('_unknown') is None
        assert len(service_node_2['unit_count']['municipality']) == 2
        assert len(service_node_2['unit_count']['city_as_department']) == 1

        assert service_node_3['unit_count']['total'] == 2
        assert service_node_3['unit_count']['municipality']['a'] == 1
        assert service_node_3['unit_count']['municipality']['c'] == 1
        assert service_node_3['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 1
        assert service_node_3['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 1
        assert service_node_3['unit_count']['city_as_department']['_unknown'] == 1
        assert len(service_node_3['unit_count']['municipality']) == 2
        assert len(service_node_3['unit_count']['city_as_department']) == 3

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

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 2
    assert service_node_1['unit_count']['municipality']['a'] == 1
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 2
    assert service_node_1['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 2
    assert len(service_node_1['unit_count']['municipality']) == 2
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_2['unit_count']['total'] == 1
    assert service_node_2['unit_count']['municipality'].get('a') is None
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert service_node_2['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 1
    assert service_node_2['unit_count']['city_as_department'].get('_unknown') is None
    assert len(service_node_2['unit_count']['municipality']) == 1
    assert len(service_node_2['unit_count']['city_as_department']) == 1

    assert service_node_3['unit_count']['total'] == 2
    assert service_node_3['unit_count']['municipality']['a'] == 1
    assert service_node_3['unit_count']['municipality']['c'] == 1
    assert service_node_3['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 1
    assert service_node_3['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 1
    assert service_node_3['unit_count']['city_as_department']['_unknown'] == 1
    assert len(service_node_3['unit_count']['municipality']) == 2
    assert len(service_node_3['unit_count']['city_as_department']) == 3

    # From service node 3 remove all units (delete unit) (from service node 1 remove units 5 and 6)
    Unit.objects.get(pk=5).delete()
    Unit.objects.get(pk=6).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 1
    assert service_node_1['unit_count']['municipality'].get('a') is None
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 1
    assert service_node_1['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 1
    assert len(service_node_1['unit_count']['municipality']) == 1
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_2['unit_count']['total'] == 1
    assert service_node_2['unit_count']['municipality'].get('a') is None
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert service_node_2['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 1
    assert service_node_2['unit_count']['city_as_department'].get('_unknown') is None
    assert len(service_node_2['unit_count']['municipality']) == 1
    assert len(service_node_2['unit_count']['city_as_department']) == 1

    assert service_node_3['unit_count']['total'] == 0
    assert len(service_node_3['unit_count']['municipality']) == 0
    assert len(service_node_3['unit_count']['city_as_department']) == 0

    # From service node 2 remove unit with muncipality None
    Unit.objects.get(pk=3).delete()
    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])

    service_node_1 = service_nodes[0]
    service_node_2 = service_nodes[1]
    service_node_3 = service_nodes[2]

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 1
    assert service_node_1['unit_count']['municipality'].get('a') is None
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 1
    assert service_node_1['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 1
    assert len(service_node_1['unit_count']['municipality']) == 1
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_2['unit_count']['total'] == 0
    assert service_node_2['unit_count']['municipality'].get('a') is None
    assert service_node_2['unit_count']['municipality'].get('c') is None
    assert service_node_2['unit_count']['city_as_department'].get('da792f32-6da7-4804-8059-16491b1ec0fa') is None
    assert len(service_node_2['unit_count']['municipality']) == 0
    assert len(service_node_2['unit_count']['city_as_department']) == 0

    assert service_node_3['unit_count']['total'] == 0
    assert len(service_node_3['unit_count']['municipality']) == 0
    assert len(service_node_3['unit_count']['city_as_department']) == 0


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

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 3
    assert service_node_1['unit_count']['municipality']['a'] == 2
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 3
    assert service_node_1['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 2
    assert len(service_node_1['unit_count']['municipality']) == 2
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_2['unit_count']['total'] == 2
    assert service_node_2['unit_count']['municipality']['a'] == 1
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert service_node_2['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 2
    assert service_node_2['unit_count']['city_as_department'].get('_unknown') is None
    assert len(service_node_2['unit_count']['municipality']) == 2
    assert len(service_node_2['unit_count']['city_as_department']) == 1

    assert service_node_3['unit_count']['total'] == 6
    assert service_node_3['unit_count']['municipality']['a'] == 3
    assert service_node_3['unit_count']['municipality']['b'] == 1
    assert service_node_3['unit_count']['municipality']['c'] == 1
    assert service_node_3['unit_count']['municipality']['_unknown'] == 1
    assert service_node_3['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 5
    assert service_node_3['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 2
    assert service_node_3['unit_count']['city_as_department']['_unknown'] == 1
    assert len(service_node_3['unit_count']['municipality']) == 4
    assert len(service_node_3['unit_count']['city_as_department']) == 3


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

    assert service_node_1['id'] == 1
    assert service_node_2['id'] == 2
    assert service_node_1['unit_count']['total'] == 0
    assert len(service_node_1['unit_count']['municipality']) == 0
    assert len(service_node_1['unit_count']['city_as_department']) == 0

    assert service_node_2['unit_count']['total'] == 2
    assert service_node_2['unit_count']['municipality']['a'] == 1
    assert service_node_2['unit_count']['municipality']['_unknown'] == 1
    assert service_node_2['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 2
    assert service_node_2['unit_count']['city_as_department'].get('_unknown') is None
    assert len(service_node_2['unit_count']['municipality']) == 2
    assert len(service_node_2['unit_count']['city_as_department']) == 1

    assert service_node_3['unit_count']['total'] == 2
    assert service_node_3['unit_count']['municipality']['a'] == 1
    assert service_node_3['unit_count']['municipality']['c'] == 1
    assert service_node_3['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 1
    assert service_node_3['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 1
    assert service_node_3['unit_count']['city_as_department']['_unknown'] == 1
    assert len(service_node_3['unit_count']['municipality']) == 2
    assert len(service_node_3['unit_count']['city_as_department']) == 3


@pytest.mark.django_db
def test_service_node_counts_nested_service_nodes(units, api_client):
    # Create service node 4 with service node 1 as a parent. Add node 4 to unit 4
    sn1_obj = ServiceNode.objects.get(pk=1)
    sn4_obj, created = ServiceNode.objects.get_or_create(id=4, name_fi='ServiceNode 4', last_modified_time=MOD_TIME,
                                                         parent=sn1_obj)
    u4_obj = Unit.objects.get(pk=4)
    u4_obj.service_nodes.add(sn4_obj)

    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])
    service_node_1 = service_nodes[0]
    service_node_4 = service_nodes[3]
    print(service_node_1)

    assert service_node_1['id'] == 1
    assert service_node_4['id'] == 4
    assert service_node_1['unit_count']['total'] == 4
    assert service_node_1['unit_count']['municipality']['a'] == 3
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 4
    assert service_node_1['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 2
    assert len(service_node_1['unit_count']['municipality']) == 2
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    # Create service node 5 with service node 4 as a parent. Add node 5 to unit 5
    # Same unit in parent and child shouldn't add to total
    sn5_obj, created = ServiceNode.objects.get_or_create(id=5, name_fi='ServiceNode 5', last_modified_time=MOD_TIME,
                                                         parent=sn4_obj)
    u5_obj = Unit.objects.get(pk=5)
    u5_obj.service_nodes.add(sn5_obj)

    update_service_node_counts()

    service_nodes = sorted(get_nodes(api_client), key=lambda x: x['id'])
    service_node_4 = service_nodes[3]
    service_node_5 = service_nodes[4]
    print(service_node_4)

    assert service_node_1['id'] == 1
    assert service_node_4['id'] == 4
    assert service_node_5['id'] == 5
    assert service_node_1['unit_count']['total'] == 4
    assert service_node_1['unit_count']['municipality']['a'] == 3
    assert service_node_1['unit_count']['municipality']['b'] == 1
    assert service_node_1['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 4
    assert service_node_1['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 2
    assert len(service_node_1['unit_count']['municipality']) == 2
    assert len(service_node_1['unit_count']['city_as_department']) == 2

    assert service_node_4['unit_count']['total'] == 2
    assert service_node_4['unit_count']['municipality']['a'] == 2
    assert service_node_4['unit_count']['municipality'].get('b') is None
    assert service_node_4['unit_count']['city_as_department']['da792f32-6da7-4804-8059-16491b1ec0fa'] == 2
    assert service_node_4['unit_count']['city_as_department']['92f9182e-0942-4d82-8b6a-09499fe9c46a'] == 1
    assert len(service_node_4['unit_count']['municipality']) == 2
    assert len(service_node_4['unit_count']['city_as_department']) == 2
