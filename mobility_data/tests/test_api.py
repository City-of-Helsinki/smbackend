import pytest
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_content_type(api_client, content_types):
    url = reverse("mobility_data:content_types-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["results"]) == len(content_types)
    result = response.json()["results"][0]
    assert result["type_name"] == "Test"
    assert result["name"] == "fi"
    assert result["name_sv"] == "sv"
    assert result["name_en"] == "en"
    assert result["description"] == "test content type"


@pytest.mark.django_db
def test_group_type(api_client, group_type):
    url = reverse("mobility_data:group_types-list")
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["type_name"] == "TestGroup"
    assert result["description"] == "test group type"


@pytest.mark.django_db
def test_mobile_unit(api_client, mobile_units, content_types, unit):
    url = reverse("mobility_data:mobile_units-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["results"]) == len(mobile_units)
    url = reverse(
        "mobility_data:mobile_units-detail",
        args=["aa6c2903-d36f-4c61-b828-19084fc7a64b"],
    )
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Test mobileunit"
    assert result["description"] == "Test description"
    assert result["content_types"][0]["id"] == str(content_types[0].id)
    assert result["extra"]["test_string"] == "4242"
    assert result["extra"]["test_int"] == 4242
    assert result["extra"]["test_float"] == 42.42
    assert "POINT" in result["geometry"]
    url = reverse(
        "mobility_data:mobile_units-detail",
        args=["ba6c2903-d36f-4c61-b828-19084fc7a64b"],
    )
    response = api_client.get(url)
    assert response.status_code == 200
    # Test multiple content types
    result = response.json()
    assert len(result["content_types"]) == 2
    assert result["content_types"][0]["type_name"] == "Test"
    assert result["content_types"][1]["type_name"] == "Test2"
    # Test string in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test&extra__test_string=4242"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"] == "Test mobileunit"
    # Test int value in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test&extra__test_int=4242"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"] == "Test mobileunit"
    # Test float value in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test&extra__test_float=42.42"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"] == "Test mobileunit"
    # Test vool value in extra field
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?type_name=Test&extra__test_bool=True"
    )
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"] == "Test2 mobileunit"
    # Test that we get a mobile unit inside bbox.
    url = (
        reverse("mobility_data:mobile_units-list")
        + "?bbox=21.1,59.2,22.3,61.4&bbox_srid=4326"
    )
    response = api_client.get(url)
    assert len(response.json()["results"]) == 1
    # Test bbox where no mobile units are inside.
    url = reverse("mobility_data:mobile_units-list") + "?bbox=22.3,61.4,23,62.4"
    response = api_client.get(url)
    assert len(response.json()["results"]) == 0
    # Test data serialization from services_unit model
    url = reverse(
        "mobility_data:mobile_units-detail",
        args=["ca6c2903-d36f-4c61-b828-19084fc7a64b"],
    )
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Test unit"
    assert result["description"] == "desc"
    assert result["content_types"][0]["type_name"] == "TestUnit"
    assert result["geometry"] == "POINT (24.24 62.22)"
    assert result["geometry_coords"]["lon"] == 24.24
    assert result["geometry_coords"]["lat"] == 62.22
    # Test only param
    url = reverse("mobility_data:mobile_units-list") + "?only=name,geometry"
    response = api_client.get(url)
    # 'id' is always serialized, so the length will be 3
    assert len(response.json()["results"][0]) == 3
    assert len(response.json()["results"][1]) == 3
    # Test retrieving multiple content types
    url = reverse("mobility_data:mobile_units-list") + "?type_names=Test,Test2"
    response = api_client.get(url)
    assert len(response.json()["results"]) == 2


@pytest.mark.django_db
def test_mobile_unit_group(api_client, mobile_unit_group, group_type):
    url = reverse("mobility_data:mobile_unit_groups-list")
    response = api_client.get(url)
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["name"] == "Test mobileunitgroup"
    assert result["description"] == "Test description"
    assert result["group_type"]["id"] == str(group_type.id)
