import pytest

from rest_framework.test import APIClient
from services.models import Unit, Department, ServiceNode, Service, UnitServiceDetails
from datetime import datetime
from munigeo.models import Municipality, AdministrativeDivisionType, AdministrativeDivision

TODAY = datetime.now()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def municipalities():
    t, created = AdministrativeDivisionType.objects.get_or_create(id=1, type='muni', defaults={'name': 'Municipality'})
    for i in range(3):
        n = str(i)
        a, created = AdministrativeDivision.objects.get_or_create(type=t, id=i, name_fi='muni_' + n,
                                                                  ocd_id='ocd-division/country:fi/kunta:muni_' + n)
        if created:
            Municipality.objects.get_or_create(id='muni_' + n, name_fi='muni_' + n, division=a)
    # print('MUNIS', Municipality.objects.all().order_by('pk'))
    return Municipality.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def departments(municipalities):
    deps = ['da792f32-6da7-4804-8059-16491b1ec0fa', '92f9182e-0942-4d82-8b6a-09499fe9c46a',
            '13108190-6157-4205-ad8e-1b92c084673a']
    for i in range(len(deps)):
        Department.objects.get_or_create(uuid=deps[i], name='dep_' + str(i), municipality=municipalities[i])
    # print('DEPS', Department.objects.all().order_by('pk'))
    return Department.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def service_nodes():
    for i in range(4):
        ServiceNode.objects.create(id=i, name='servicenode_' + str(i), last_modified_time=TODAY)
    # print('SERVICENODES', ServiceNode.objects.values())
    return ServiceNode.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def services():
    for i in range(4):
        Service.objects.get_or_create(id=i, name='service_' + str(i), last_modified_time=TODAY)
    # print('SERVICE', Service.objects.values())
    return Service.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def units(municipalities, departments, service_nodes, services):
    u1, _ = Unit.objects.get_or_create(pk=0, name_fi='unit_0', municipality=municipalities[0],
                                       root_department=departments[0], provider_type=1,
                                       last_modified_time=TODAY)
    u2, _ = Unit.objects.get_or_create(pk=1, name_fi='unit_1', municipality=municipalities[1],
                                       root_department=departments[1], provider_type=2,
                                       last_modified_time=TODAY)
    u3, _ = Unit.objects.get_or_create(pk=2, name_fi='unit_2', municipality=municipalities[2],
                                       root_department=departments[2], provider_type=3,
                                       last_modified_time=TODAY)
    u4, _ = Unit.objects.get_or_create(pk=3, name_fi='unit_3', municipality=municipalities[2],
                                       root_department=departments[2], provider_type=3,
                                       last_modified_time=TODAY)
    unis = Unit.objects.all().order_by('pk')
    for i in range(len(unis)):
        # u, _ = Unit.objects.get_or_create(pk=i, name_fi='unit_' + str(i), municipality=municipalities[i % 2],
        #                                   root_department=departments[i % 2], provider_type=i % 2 + 1,
        #                                   last_modified_time=TODAY)
        unis[i].service_nodes.add(service_nodes[i])
        # print('UUUUNNNNN', service_nodes[i].units.all())
    # print('NODE', service_nodes[0].units.all())
    # print('UNITS', Unit.objects.values())
    # print('SERVICENODES', ServiceNode.objects.values())
    # print('SERVICE', Service.objects.values())
    return Unit.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def unit_service_details(units, services):
    for i in range(len(units)):
        UnitServiceDetails.objects.get_or_create(unit=units[i], service=services[i])
    # print('SERVICEDETAILS', UnitServiceDetails.objects.values())
    # print('UNITS', Unit.objects.values())
    return UnitServiceDetails.objects.all().order_by('pk')
