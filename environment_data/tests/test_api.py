import pytest
from rest_framework.reverse import reverse

from environment_data.constants import AIR_QUALITY, DATA_TYPES_FULL_NAME


@pytest.mark.django_db
def test_station(api_client, stations, year_datas):
    url = reverse("environment_data:stations-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 2
    url = reverse("environment_data:stations-list") + f"?data_type={AIR_QUALITY}"
    response = api_client.get(url)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["count"] == 1
    result = json_data["results"][0]
    assert result["data_type"] == AIR_QUALITY
    assert result["data_type_verbose"] == DATA_TYPES_FULL_NAME[AIR_QUALITY]
    assert result["name"] == "Test"
    assert result["parameters_in_use"]["AQINDEX_PT1H_avg"] is True
    assert result["parameters_in_use"]["NO2_PT1H_avg"] is False


@pytest.mark.django_db
def test_hour_data(api_client, hour_datas, parameters):
    url = (
        reverse("environment_data:data-list")
        + "?year=2023&start=01-01&end=02-01&station_id=1&type=hour"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    json_data = response.json()["results"][0]
    assert len(json_data["measurements"]) == 1
    assert json_data["measurements"][0]["value"] == 1.5
    assert json_data["measurements"][0]["parameter"] == parameters[0].name
    assert json_data["hour_number"] == 0
    assert json_data["date"] == "2023-01-01"


@pytest.mark.django_db
def test_day_data(api_client, day_datas, parameters):
    url = (
        reverse("environment_data:data-list")
        + "?year=2023&start=01-01&end=02-01&station_id=1&type=day"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    json_data = response.json()["results"][0]
    assert len(json_data["measurements"]) == 1
    assert json_data["measurements"][0]["value"] == 1.5
    assert json_data["measurements"][0]["parameter"] == parameters[0].name
    assert json_data["date"] == "2023-01-01"


@pytest.mark.django_db
def test_week_data(api_client, week_datas, parameters):
    url = (
        reverse("environment_data:data-list")
        + "?year=2023&start=1&end=1&station_id=1&type=week"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    json_data = response.json()["results"][0]
    assert len(json_data["measurements"]) == 1
    assert json_data["measurements"][0]["value"] == 1.5
    assert json_data["measurements"][0]["parameter"] == parameters[0].name
    assert json_data["week_number"] == 1


@pytest.mark.django_db
def test_month_data(api_client, month_datas, parameters):
    url = (
        reverse("environment_data:data-list")
        + "?year=2023&start=1&end=1&station_id=1&type=month"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    json_data = response.json()["results"][0]
    assert len(json_data["measurements"]) == 1
    assert json_data["measurements"][0]["value"] == 1.5
    assert json_data["measurements"][0]["parameter"] == parameters[0].name
    assert json_data["month_number"] == 1


@pytest.mark.django_db
def test_year_data(api_client, year_datas, parameters):
    url = (
        reverse("environment_data:data-list")
        + "?start=2023&end=2023&station_id=1&type=year"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    json_data = response.json()["results"][0]
    assert len(json_data["measurements"]) == 1
    assert json_data["measurements"][0]["value"] == 1.5
    assert json_data["measurements"][0]["parameter"] == parameters[0].name
    assert json_data["year_number"] == 2023
