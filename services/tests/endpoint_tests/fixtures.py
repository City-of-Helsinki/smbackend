import pytest

from django.utils.timezone import now
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from rest_framework.test import APIClient

from munigeo.models import AdministrativeDivisionType, AdministrativeDivision, AdministrativeDivisionGeometry, \
    Municipality
from services.models import Unit, Department, ServiceNode, Service, UnitServiceDetails

TODAY = now()
data = {'bbox': [[24.916821, 60.163376, 24.960937, 60.185233],
                 [24.818115, 60.179770, 24.840045, 60.190695],
                 [24.785500, 60.272642, 25.004797, 60.342920]],
        'departments': ['da792f32-6da7-4804-8059-16491b1ec0fa', '92f9182e-0942-4d82-8b6a-09499fe9c46a',
                        '13108190-6157-4205-ad8e-1b92c084673a'],
        'municipalities': ['muni_0', 'muni_1', 'muni_2']
        }


@pytest.fixture
def api_client():
    return APIClient()

# test set-up; IDs for units, municipalities, services, service nodes

#  u | m | s  | s_n_tree(parent)
# ---+---+----+----------
#  0 | 0 | 0  | 0
# ---+---+----+----------
#  1 | 1 | 1  | 1(0)
# ---+---+----+----------
#  2 | 2 | 2,3| 2(1)
# ---+---+----+----------
#  3 | 0 | _  | 3
# -----------------------


@pytest.fixture
@pytest.mark.django_db
def municipalities():
    bbox = [MultiPolygon(Polygon.from_bbox(tuple(bbox)), srid=4326) for bbox in data['bbox']]

    t, created = AdministrativeDivisionType.objects.get_or_create(id=1, type='muni', defaults={'name': 'Municipality'})
    for i in range(3):
        n = str(i)
        a, _ = AdministrativeDivision.objects.get_or_create(type=t, id=i, name_fi='muni_' + n,
                                                            ocd_id='ocd-division/country:fi/kunta:muni_' + n)
        AdministrativeDivisionGeometry.objects.get_or_create(division=a, boundary=bbox[i])
        Municipality.objects.get_or_create(id='muni_' + n, name_fi='muni_' + n, division=a)
    return Municipality.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def departments(municipalities):
    deps = data['departments']
    for i in range(len(deps)):
        Department.objects.get_or_create(uuid=deps[i], name='dep_' + str(i), municipality=municipalities[i])
    return Department.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def service_nodes_flat():
    for i in range(4):
        ServiceNode.objects.create(id=i, name='servicenode_' + str(i), last_modified_time=TODAY)
    return ServiceNode.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def service_nodes_tree():
    # node_0 is parent of node_1, node_1 is parent of node_2, node_0 and node_3 have no parents
    for i in range(4):
        if i == 0 or i == 3:
            s, _ = ServiceNode.objects.get_or_create(id=i, name='servicenode_' + str(i), last_modified_time=TODAY)
        else:
            ServiceNode.objects.get_or_create(id=i, name='servicenode_' + str(i),
                                              parent=ServiceNode.objects.get(id=i - 1), last_modified_time=TODAY)
    return ServiceNode.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def services(service_nodes_tree):
    for i in range(4):
        s, _ = Service.objects.get_or_create(id=i, name='service_' + str(i), root_service_node=service_nodes_tree[i],
                                             last_modified_time=TODAY)
        service_nodes_tree[i].related_services.add(s)
    return Service.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def units(municipalities, departments):
    # ympyrätalo (muni_0)
    pnt_0 = Point(24.949593, 60.180379, srid=4326)
    # säästöpankinranta (muni_0)
    pnt_1 = Point(24.947442, 60.179162, srid=4326)
    # smökki (muni_1)
    pnt_2 = Point(24.836425604, 60.188401742, srid=4326)
    # HEL (muni_2)
    pnt_3 = Point(24.969019031, 60.326154057, srid=4326)

    u0, _ = Unit.objects.get_or_create(pk=0, name_fi='unit_0', municipality=municipalities[0], location=pnt_1,
                                       root_department=departments[0], provider_type=1,
                                       last_modified_time=TODAY)
    u1, _ = Unit.objects.get_or_create(pk=1, name_fi='unit_1', municipality=municipalities[1], location=pnt_2,
                                       root_department=departments[1], provider_type=2,
                                       last_modified_time=TODAY)
    u2, _ = Unit.objects.get_or_create(pk=2, name_fi='unit_2', municipality=municipalities[2], location=pnt_3,
                                       root_department=departments[2], provider_type=3,
                                       last_modified_time=TODAY)
    u3, _ = Unit.objects.get_or_create(pk=3, name_fi='unit_3', municipality=municipalities[0], location=pnt_0,
                                       root_department=departments[1], provider_type=3,
                                       last_modified_time=TODAY)
    return Unit.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def units_service_nodes_flat(units, service_nodes_flat):
    unis = Unit.objects.all().order_by('pk')
    for i in range(len(unis)):
        unis[i].service_nodes.add(service_nodes_flat[i])


@pytest.fixture
@pytest.mark.django_db
def units_service_nodes_tree(units, service_nodes_tree):
    unis = Unit.objects.all().order_by('pk')
    for i in range(len(unis)):
        unis[i].service_nodes.add(service_nodes_tree[i])


@pytest.fixture
@pytest.mark.django_db
def unit_service_details(units, services):
    # unit_0 assigned to service_0, unit_1 assigned to service_1,
    # unit_2 assigned to service_2 and service_3, unit_3 not assigned to any service
    for i in range(len(units) - 1):
        UnitServiceDetails.objects.get_or_create(unit=units[i], service=services[i])
    UnitServiceDetails.objects.get_or_create(unit=units[2], service=services[3])
    return UnitServiceDetails.objects.all().order_by('pk')
