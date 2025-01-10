import datetime as d

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from munigeo.models import Municipality
from rest_framework.test import APIClient

from observations.models import (
    AllowedValue,
    CategoricalObservation,
    DescriptiveObservation,
    ObservableProperty,
    UnitLatestObservation,
    UserOrganization,
)
from services.models import Department, Service, Unit, UnitServiceDetails


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    username = "test_user"
    password = "test_password"
    municipality = "helsinki"
    user = User.objects.create(username=username)
    municipality = Municipality.objects.create(id=municipality, name=municipality)
    organization = Department.objects.create(
        name_fi="test_org",
        municipality=municipality,
        uuid="063c6150-ccc7-4886-b44b-ecee7670d065",
    )
    UserOrganization.objects.create(user=user, organization=organization)
    user.set_password(password)
    user.save()
    return {"username": username, "password": password}


@pytest.fixture
def organization():
    return Department.objects.create(
        name="Fors", uuid="063c6150-ccc7-4886-b44b-ecee7670d064"
    )


@pytest.fixture
def service():
    return Service.objects.create(
        id=1, name="skiing", last_modified_time=timezone.now()
    )


@pytest.fixture
def unit(service, organization):
    unit = Unit.objects.create(
        id=1,
        name="skiing place",
        last_modified_time=timezone.now(),
        provider_type=1,
        department=organization,
    )
    UnitServiceDetails(unit=unit, service=service).save()
    return unit


@pytest.fixture
def categorical_observations(unit, observable_property):
    return [
        CategoricalObservation.objects.create(
            time=timezone.now() - d.timedelta(days=1),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value("good"),
        ),
        CategoricalObservation.objects.create(
            time=timezone.now() - d.timedelta(days=2),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value("poor"),
        ),
        CategoricalObservation.objects.create(  # Not expired
            time=timezone.now() - d.timedelta(minutes=599),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value("closed"),
        ),
        CategoricalObservation.objects.create(  # Expired
            time=timezone.now() - d.timedelta(minutes=600),
            unit=unit,
            property=observable_property,
            value=observable_property.get_internal_value("closed"),
        ),
    ]


@pytest.fixture
def descriptive_observations(unit, descriptive_property):
    value = AllowedValue.objects.create(
        identifier=None,
        name="No name",
        description="Description",
        property=descriptive_property,
    )
    return [
        DescriptiveObservation.objects.create(
            time=timezone.now() - d.timedelta(days=100),
            unit=unit,
            property=descriptive_property,
            value=value,
        )
    ]


@pytest.fixture
def observable_property(service, unit):
    p = ObservableProperty.objects.create(
        id="skiing_trail_condition",
        name="Skiing trail condition",
        expiration=d.timedelta(hours=10),
        observation_type="observations.CategoricalObservation",
    )
    p.services.add(service)
    (
        AllowedValue.objects.create(
            identifier="no_snow",
            name="No snow",
            description="There is no snow",
            property=p,
        ),
    )
    (
        AllowedValue.objects.create(
            identifier="good",
            name="Good condition",
            description="The trail is in good condition",
            property=p,
        ),
    )
    (
        AllowedValue.objects.create(
            identifier="poor",
            name="Poor condition",
            description="Poor skiing condition",
            property=p,
        ),
    )
    AllowedValue.objects.create(
        identifier="closed",
        name="Closed",
        description="The trail is closed",
        property=p,
    )
    return p


@pytest.fixture
def unit_latest_observation(observable_property, unit, categorical_observations):
    return UnitLatestObservation.objects.create(
        observation=categorical_observations[2], property=observable_property, unit=unit
    )


@pytest.fixture
def unit_latest_observation_expired(
    observable_property, unit, categorical_observations
):
    return UnitLatestObservation.objects.create(
        observation=categorical_observations[3], property=observable_property, unit=unit
    )


@pytest.fixture
def unit_latest_observation_both_expired_and_not_expirable(
    descriptive_property,
    descriptive_observations,
    unit,
    unit_latest_observation_expired,
):
    latest_observation = UnitLatestObservation.objects.create(
        observation=descriptive_observations[0],
        property=descriptive_property,
        unit=unit,
    )
    return {
        "expired": unit_latest_observation_expired,
        "not_expirable": latest_observation,
    }


@pytest.fixture
def descriptive_property(service, unit):
    p = ObservableProperty.objects.create(
        id="notice",
        name="Notice",
        observation_type="observations.DescriptiveObservation",
    )
    p.services.add(service)
    return p
