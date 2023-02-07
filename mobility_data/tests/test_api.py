import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_content_type(api_client, content_type):
    url = reverse("mobility_data:content_types-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"][0]
    assert results["name"] == "Test"
    assert results["description"] == "test content type"


@pytest.mark.django_db
def test_group_type(api_client, group_type):
    url = reverse("mobility_data:group_types-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"][0]
    assert results["name"] == "TestGroup"
    assert results["description"] == "test group type"


@pytest.mark.django_db
def test_mobile_unit(api_client, mobile_unit, content_type):
    url = reverse("mobility_data:mobile_units-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"][0]
    assert results["name"] == "Test mobileunit"
    assert results["description"] == "Test description"
    assert results["content_type"]["id"] == str(content_type.id)
    assert results["extra"]["test_string"] == "4242"
    assert results["extra"]["test_int"] == 4242
    assert results["extra"]["test_float"] == 42.42
    assert results["geometry"] == Point(
        235404.6706163187, 6694437.919005549, srid=settings.DEFAULT_SRID
    )
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test?extra__test_string=4242"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"][0]
    assert results["name"] == "Test mobileunit"
    # Test int value in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test?extra__test_int=4242"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"][0]
    assert results["name"] == "Test mobileunit"
    # Test float value in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test?extra__test_float=42.42"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"][0]
    assert results["name"] == "Test mobileunit"
    # Test that we get a mobile unit inside bbox.
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?bbox=21.1,59.2,22.3,61.4&bbox_srid=4326"
    )
    response = api_client.get(url)
    assert len(response.json()["results"]) == 1
    # Test bbox where no mobile units are inside.
    url = reverse("mobility_data:mobile_units-list") + "?bbox=22.1,60.2,2.3,60.4"
    response = api_client.get(url)
    assert len(response.json()["results"]) == 0


@pytest.mark.django_db
def test_mobile_unit_group(api_client, mobile_unit_group, group_type):
    url = reverse("mobility_data:mobile_unit_groups-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"][0]
    assert results["name"] == "Test mobileunitgroup"
    assert results["description"] == "Test description"
    assert results["group_type"]["id"] == str(group_type.id)
