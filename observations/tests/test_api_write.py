import pytest
from datetime import datetime, timedelta
from django.urls import reverse as django_reverse
from django.utils import timezone
from fixtures import *  # noqa: F401,F403
from rest_framework.reverse import reverse

from data import observation_raw_data
from observations.models import Observation
from services.models import Unit


def authenticate_user(api_client, user):
    url = django_reverse("api-auth-token")
    response = api_client.post(url, user)
    token = response.data["token"]
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token)


@pytest.mark.django_db
def test__create_observation(api_client, observable_property, unit, user):
    url = (
        reverse("unit-detail", kwargs={"pk": unit.pk})
        + "?include=observable_properties"
    )
    response = api_client.get(url)
    observable_properties = response.data["observable_properties"]
    assert len(observable_properties) > 0
    assert Observation.objects.count() == 0

    authenticate_user(api_client, user)

    count = 0
    for prop in observable_properties:
        otype = prop["id"]
        allowed_values = [v["identifier"] for v in prop["allowed_values"]] + [None]
        for raw_data in observation_raw_data(
            otype, unit, allowed_values=allowed_values
        ):
            url = reverse("observation-list")
            current_time = timezone.now()
            response = api_client.post(url, raw_data, format="json")

            assert response.status_code == 201
            count += 1
            data = response.data
            observation_time = datetime.strptime(data["time"], "%Y-%m-%dT%H:%M:%S.%f%z")
            assert observation_time - current_time < timedelta(seconds=1)
            assert data["value"] == raw_data["value"]
            assert data["property"] == raw_data["property"]
            assert data["unit"] == raw_data["unit"]
    assert count > 0
    assert Observation.objects.count() == count


@pytest.mark.django_db
def test__create_descriptive_observation(api_client, descriptive_property, unit, user):
    url = (
        reverse("unit-detail", kwargs={"pk": unit.pk})
        + "?include=observable_properties"
    )
    response = api_client.get(url)
    observable_properties = response.data["observable_properties"]
    assert len(observable_properties) > 0
    assert Observation.objects.count() == 0

    authenticate_user(api_client, user)

    count = 0
    for prop in observable_properties:
        url = reverse("observation-list")
        current_time = timezone.now()

        # Test default language

        raw_data = dict(unit=unit.pk, value="test string", property=prop["id"])
        response = api_client.post(url, raw_data, format="json")
        assert response.status_code == 201
        count += 1
        data = response.data
        observation_time = datetime.strptime(data["time"], "%Y-%m-%dT%H:%M:%S.%f%z")

        assert observation_time - current_time < timedelta(seconds=1)
        assert data["value"]["fi"] == raw_data["value"]
        assert data["property"] == raw_data["property"]
        assert data["unit"] == raw_data["unit"]

        current_time = timezone.now()

        # Test all + 1 languages
        raw_data = dict(
            unit=unit.pk,
            value={"fi": "test string", "en": "test string 2", "sv": "test string 3"},
            property=prop["id"],
        )
        response = api_client.post(url, raw_data, format="json")
        assert response.status_code == 201
        count += 1
        data = response.data
        observation_time = datetime.strptime(data["time"], "%Y-%m-%dT%H:%M:%S.%f%z")

        assert observation_time - current_time < timedelta(seconds=1)
        assert data["value"] == raw_data["value"]
        assert data["property"] == raw_data["property"]
        assert data["unit"] == raw_data["unit"]

    assert Observation.objects.count() == count


@pytest.mark.django_db(transaction=True)
def test__delete_unit_with_observation_link(categorical_observations, unit):
    assert Unit.objects.count() == 1
    assert Observation.objects.count() == 4
    unit.delete()
    assert Unit.objects.count() == 1
    assert Observation.objects.count() == 4
    deleted_unit = Unit.objects.filter(name="DELETED_UNIT").first()
    for observation in Observation.objects.all():
        assert observation.unit == deleted_unit
