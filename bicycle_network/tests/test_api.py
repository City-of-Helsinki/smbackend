import pytest
from rest_framework.reverse import reverse
from bicycle_network.tests.fixtures import *


@pytest.mark.django_db
def test_bicycle_network(api_client, bicycle_network):
    url = reverse("bicycle_network:bicycle_networks-list")
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["name_fi"] == "local_network"
    assert results[1]["name_fi"] == "main_network"
    assert results[1]["name_sv"] == "huvudnätverk"


@pytest.mark.django_db
def test_bicycle_network_part(api_client, bicycle_network, bicycle_network_part):
    url = reverse("bicycle_network:bicycle_networkparts-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 2
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?name=main_network"
    )
    response = api_client.get(url)
    # One part in main_network
    assert response.json()["count"] == 1
    # query with bbox including both parts
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?bbox=22.0,59.8,22.3,60.4"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 2
    # query with bbox including only one part
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?bbox=22.2,60.2,22.3,60.4"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 1
    # query with bbox outside the generated lines
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?bbox=22.4,60.5,22.5,60.7"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 0
    # query for parts that are completly inside 1000m radius from point 22.25,60.3
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?lon=22.25&lat=60.3&distance=1000"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 1
    # query for parts that are completly inside 12000m radius from point 22.1,60.1
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?lon=22.1&lat=60.1&distance=120000"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 2
    # query for parts that are completly inside 1000m radius from point 22.1,60.1. None are inside.
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?lon=22.1&lat=60.1&distance=1000"
    )
    response = api_client.get(url)
    assert response.json()["count"] == 0
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?name=local_network&only_coords=true"
    )
    response = api_client.get(url)
    # only 'id' and 'geometry_coords' filed in results with only_coords set to true in query
    assert len(response.json()["results"][0]) == 2
    # test latlon = true, e.g. linestrings coords are in lat,lon format.
    url = (
        reverse("bicycle_network:bicycle_networkparts-list")
        + "?name=main_network&latlon=true"
    )
    response = api_client.get(url)
    lon = bicycle_network_part[0].geometry.coords[0][0]
    lat = bicycle_network_part[0].geometry.coords[0][1]
    geom = response.json()["results"][0]["geometry_coords"]
    assert lat == geom[0][0]
    assert lon == geom[0][1]
