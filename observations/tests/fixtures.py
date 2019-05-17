import pytest
from rest_framework.test import APIClient
from services.models import Service, Unit, Department, UnitServiceDetails
from observations.models import (
    ObservableProperty, CategoricalObservation, AllowedValue,
    UserOrganization, UnitLatestObservation
)
import datetime as d
from django.contrib.auth.models import User
from munigeo.models import Municipality


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def user():
    USERNAME = 'test_user'
    PASSWORD = 'test_password'
    MUNICIPALITY = 'helsinki'
    user = User.objects.create(username=USERNAME)
    municipality = Municipality.objects.create(id=MUNICIPALITY, name=MUNICIPALITY)
    organization = Department.objects.create(name_fi='test_org', municipality=municipality,
                                             uuid='063c6150-ccc7-4886-b44b-ecee7670d065')
    UserOrganization.objects.create(user=user, organization=organization)
    user.set_password(PASSWORD)
    user.save()
    return {'username': USERNAME, 'password': PASSWORD}


@pytest.mark.django_db
@pytest.fixture
def organization():
    return Department.objects.create(
        name='Fors',
        uuid='063c6150-ccc7-4886-b44b-ecee7670d064')


@pytest.mark.django_db
@pytest.fixture
def service():
    return Service.objects.create(
        id=1,
        name='skiing',
        last_modified_time=d.datetime.now())


@pytest.mark.django_db
@pytest.fixture
def unit(service, organization):
    unit = Unit.objects.create(
        id=1,
        name='skiing place',
        last_modified_time=d.datetime.now(),
        provider_type=1,
        department=organization)
    UnitServiceDetails(unit=unit, service=service).save()
    return unit


@pytest.mark.django_db
@pytest.fixture
def categorical_observations(unit, observable_property):
    return [
        CategoricalObservation.objects.create(
            time=d.datetime.now() - d.timedelta(days=1),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value('good')),
        CategoricalObservation.objects.create(
            time=d.datetime.now() - d.timedelta(days=2),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value('poor')),
        CategoricalObservation.objects.create(
            time=d.datetime.now() - d.timedelta(days=3),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value('closed')),
        CategoricalObservation.objects.create(
            time=d.datetime.now() - d.timedelta(days=11),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value('closed'))]


@pytest.mark.django_db
@pytest.fixture
def observable_property(service, unit):
    p = ObservableProperty.objects.create(
        id='skiing_trail_condition',
        name='Skiing trail condition',
        expiration=d.timedelta(days=10),
        observation_type='observations.CategoricalObservation'
    )
    p.services.add(service)
    AllowedValue.objects.create(
        identifier='no_snow',
        name='No snow',
        description='There is no snow',
        property=p
    ),
    AllowedValue.objects.create(
        identifier='good',
        name='Good condition',
        description='The trail is in good condition',
        property=p
    ),
    AllowedValue.objects.create(
        identifier='poor',
        name='Poor condition',
        description='Poor skiing condition',
        property=p
    ),
    AllowedValue.objects.create(
        identifier='closed',
        name='Closed',
        description='The trail is closed',
        property=p
    )
    return p


@pytest.mark.django_db
@pytest.fixture
def unit_latest_observation(observable_property, unit, categorical_observations):
    return UnitLatestObservation.objects.create(
        observation=categorical_observations[2],
        property=observable_property,
        unit=unit
    )


@pytest.mark.django_db
@pytest.fixture
def unit_latest_observation_expired(observable_property, unit, categorical_observations):
    return UnitLatestObservation.objects.create(
        observation=categorical_observations[3],
        property=observable_property,
        unit=unit
    )


@pytest.mark.django_db
@pytest.fixture
def descriptive_property(service, unit):
    p = ObservableProperty.objects.create(
        id='notice',
        name='Notice',
        observation_type='observations.DescriptiveObservation'
    )
    p.services.add(service)
    return p
