import pytest
from datetime import datetime

from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from rest_framework.test import APIClient

from services.models import Unit, Department, ServiceNode, Service, UnitServiceDetails
from munigeo.models import AdministrativeDivisionType, AdministrativeDivision, AdministrativeDivisionGeometry, \
    Municipality, Address, Street


TODAY = datetime.now()
bbox_0 = MultiPolygon(Polygon(srid=4326).from_bbox((24.863962464, 60.186704901, 24.986374646, 60.148095083)))
bbox_1 = MultiPolygon(Polygon(srid=4326).from_bbox((24.834427264, 60.153170852, 24.720668286, 60.197252873)))
bbox_2 = MultiPolygon(Polygon(srid=4326).from_bbox((24.834504387, 60.266958912, 25.067844357, 60.357068896)))


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def municipalities():
    bbox = [bbox_0, bbox_1, bbox_2]
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
def addresses(municipalities):
    pnt = Point(24.948475627, 60.180769286, srid=4326)
    t, _ = Street.objects.get_or_create(name='Porthaninrinne', municipality=municipalities[0])
    Address.objects.get_or_create(street=t, location=pnt)
    return Address.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def departments(municipalities):
    deps = ['da792f32-6da7-4804-8059-16491b1ec0fa', '92f9182e-0942-4d82-8b6a-09499fe9c46a',
            '13108190-6157-4205-ad8e-1b92c084673a']
    for i in range(len(deps)):
        Department.objects.get_or_create(uuid=deps[i], name='dep_' + str(i), municipality=municipalities[i])
    return Department.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def service_nodes():
    for i in range(4):
        ServiceNode.objects.create(id=i, name='servicenode_' + str(i), last_modified_time=TODAY)
    return ServiceNode.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def services(service_nodes):
    for i in range(4):
        s, _ = Service.objects.get_or_create(id=i, name='service_' + str(i), root_service_node=service_nodes[i],
                                             last_modified_time=TODAY)
        service_nodes[i].related_services.add(s)
    return Service.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def units(municipalities, departments, service_nodes, services):
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
                                       root_department=departments[0], provider_type=3,
                                       last_modified_time=TODAY)

    unis = Unit.objects.all().order_by('pk')
    for i in range(len(unis)):
        unis[i].service_nodes.add(service_nodes[i])
    return Unit.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def unit_service_details(units, services):
    for i in range(len(units)):
        UnitServiceDetails.objects.get_or_create(unit=units[i], service=services[i])
    return UnitServiceDetails.objects.all().order_by('pk')
