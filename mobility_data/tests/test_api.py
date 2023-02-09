import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_content_type(api_client, content_types):
    url = reverse("mobility_data:content_types-list")
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["name"] == "Test"
    assert result["description"] == "test content type"


@pytest.mark.django_db
def test_group_type(api_client, group_type):
    url = reverse("mobility_data:group_types-list")
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["name"] == "TestGroup"
    assert result["description"] == "test group type"


@pytest.mark.django_db
def test_mobile_unit(api_client, mobile_units, content_types):
    url = reverse("mobility_data:mobile_units-list")
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][1]
    assert result["name"] == "Test mobileunit"
    assert result["description"] == "Test description"
    assert result["content_types"][0]["id"] == str(content_types[0].id)
    assert result["extra"]["test_string"] == "4242"
    assert result["extra"]["test_int"] == 4242
    assert result["extra"]["test_float"] == 42.42
    assert result["geometry"] == Point(42.42, 21.21, srid=settings.DEFAULT_SRID)
    # Test multiple content types
    result = response.json()["results"][0]
    assert len(result["content_types"]) == 2
    assert result["content_types"][0]["name"] == "Test"
    assert result["content_types"][1]["name"] == "Test2"
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test?extra__test_string=4242"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][1]
    assert result["name"] == "Test mobileunit"
    # Test int value in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test?extra__test_int=4242"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][1]
    assert result["name"] == "Test mobileunit"
    # Test float value in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test?extra__test_float=42.42"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][1]
    assert result["name"] == "Test mobileunit"


@pytest.mark.django_db
def test_mobile_unit_group(api_client, mobile_unit_group, group_type):
    url = reverse("mobility_data:mobile_unit_groups-list")
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["name"] == "Test mobileunitgroup"
    assert result["description"] == "Test description"
    assert result["group_type"]["id"] == str(group_type.id)
