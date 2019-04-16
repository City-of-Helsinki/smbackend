import pytest

from rest_framework.test import APIClient
from services.models import Unit, Department
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
    for i in range(2):
        n = str(i)
        a, created = AdministrativeDivision.objects.get_or_create(type=t, id=i, name_fi='muni_'+n,
                                                                  ocd_id='ocd-division/country:fi/kunta:muni_'+n)
        if created:
            Municipality.objects.get_or_create(id='muni_'+n, name_fi='muni_'+n, division=a)
    # print('MUNIS', Municipality.objects.all().order_by('pk'))
    return Municipality.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def departments(municipalities):
    muni_0, muni_1 = municipalities
    Department.objects.get_or_create(uuid='da792f32-6da7-4804-8059-16491b1ec0fa', name='dep_0',
                                     municipality=muni_0)
    Department.objects.get_or_create(uuid='92f9182e-0942-4d82-8b6a-09499fe9c46a', name='dep_1',
                                     municipality=muni_1)
    # print('DEPS', Department.objects.all().order_by('pk'))
    return Department.objects.all().order_by('pk')


@pytest.fixture
@pytest.mark.django_db
def units(municipalities, departments):
    for i in range(len(departments)):
        Unit.objects.get_or_create(pk=i, name_fi='unit_'+str(i), municipality=municipalities[i],
                                   root_department=departments[i], last_modified_time=TODAY)
    # print('UNITS', Unit.objects.values())
    return Unit.objects.all().order_by('pk')

