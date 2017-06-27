import pytest
from rest_framework.test import APIClient
from services.models import OntologyWord, Unit, Organization
from observations.models import ObservableProperty, CategoricalObservation, AllowedValue, UserOrganization
import datetime as d
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
@pytest.fixture
def user():
    USERNAME='test_user'
    PASSWORD='test_password'
    user = User.objects.create(username=USERNAME)
    organization = Organization.objects.create(name_fi='test_org', id=1)
    UserOrganization.objects.create(user=user, organization=organization)
    user.set_password(PASSWORD)
    user.save()
    return {'username': USERNAME, 'password': PASSWORD}

@pytest.mark.django_db
@pytest.fixture
def service():
    return OntologyWord.objects.create(
        id=1,
        name='skiing',
        unit_count=1,
        last_modified_time=d.datetime.now())

@pytest.mark.django_db
@pytest.fixture
def unit():
    return Unit.objects.create(
        id=1,
        name='skiing place',
        last_modified_time=d.datetime.now())

@pytest.mark.django_db
@pytest.fixture
def unit(service):
    unit = Unit.objects.create(
        id=1,
        name='skiing place',
        origin_last_modified_time=d.datetime.now(),
        provider_type=1,
        organization_id=1)
    unit.services.add(service)
    return unit

@pytest.mark.django_db
@pytest.fixture
def categorical_observations(unit, observable_property):
    return [
        CategoricalObservation.objects.create(
            time=d.datetime.now() - d.timedelta(days=1),
            unit=unit,
            property=observable_property,
            value='good'),
        CategoricalObservation.objects.create(
            time=d.datetime.now() - d.timedelta(days=2),
            unit=unit,
            property=observable_property,
            value='poor'),
        CategoricalObservation.objects.create(
            time=d.datetime.now() - d.timedelta(days=3),
            unit=unit,
            property=observable_property,
            value='closed')]

@pytest.mark.django_db
@pytest.fixture
def observable_property(service, unit):
    p = ObservableProperty.objects.create(
        id='skiing_trail_condition',
        name='Skiing trail condition',
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
    )
    return p

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
