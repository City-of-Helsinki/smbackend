import pytest
from fixtures import *  # noqa: F401,F403
from rest_framework.reverse import reverse

from observations.models import MeasuredObservation
from observations.serializers import (
    MeasuredObservationSerializer,
    ObservationSerializer,
    get_serializer_by_object,
)


@pytest.mark.django_db
def test__measured_property_type_and_model(measured_property):
    assert measured_property.get_observation_type() == "measured"
    assert measured_property.get_observation_model() is MeasuredObservation
    # Numeric values are coerced to float.
    assert measured_property.get_internal_value("13.25") == pytest.approx(13.25)
    assert measured_property.get_internal_value(None) is None


@pytest.mark.django_db
def test__measured_observation_serializer_dispatch(measured_observations):
    obs = measured_observations[0]
    assert get_serializer_by_object(obs) is MeasuredObservationSerializer


@pytest.mark.django_db
def test__measured_observation_serialized_value(measured_observations):
    obs = measured_observations[-1]
    data = ObservationSerializer(obs, context={}).data
    assert data["value"] == pytest.approx(13.40)
    assert data["property"] == "measured_swimming_water_temperature"
    assert data["unit"] == obs.unit_id


@pytest.mark.django_db
def test__observation_endpoint_returns_measured(
    api_client, unit, measured_property, measured_observations
):
    url = (
        reverse("observation-list") + f"?unit={unit.pk}&property={measured_property.pk}"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.data["results"]
    values = sorted(item["value"] for item in results)
    assert values == pytest.approx([13.25, 13.40])
    for item in results:
        assert item["property"] == "measured_swimming_water_temperature"
        assert item["unit"] == unit.pk


@pytest.mark.django_db
def test__unit_include_observations_returns_latest_measured(
    api_client, service, measured_property, unit_latest_measured_observation
):
    url = reverse("unit-list") + f"?service={service.pk}&include=observations"
    response = api_client.get(url)
    observations = response.data["results"][0]["observations"]
    measured = [
        o
        for o in observations
        if o["property"] == "measured_swimming_water_temperature"
    ]
    assert len(measured) == 1
    assert measured[0]["value"] == pytest.approx(13.40)
