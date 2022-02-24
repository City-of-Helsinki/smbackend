import pytest
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_search(
    api_client, units, streets, services, addresses, administrative_division
):
    # Note for yet unknown reasons postgresql trigram extension is
    # not working under pytest, to overcome all test are made so that
    # trigram search is not used.

    # Search only units and services, no munigeo data in fixtures
    url = reverse("search") + "?q=museo&use_trigram=false&extended_serializer=false"
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["object_type"] == "unit"
    assert results[0]["name"]["fi"] == "Museo"
    assert results[2]["object_type"] == "service"
    assert results[2]["name"]["sv"] == "Museum"

    # Test that unit Impivara is retrived from service Uimahalli
    url = reverse("search") + "?q=uimahalli&use_trigram=false&extended_serializer=false"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results[0]["name"]["fi"] == "Impivaara"
    assert results[1]["name"]["fi"] == "Uimahalli"
    # Test address search
    url = reverse("search") + "?q=kurra&use_trigram=false"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results[0]["full_name"]["fi"] == "Kurrapolku 1A"
    assert results[0]["object_type"] == "address"
    # Test administrative division search
    url = reverse("search") + "?q=tur&use_trigram=false&extended_serializer=false"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results[0]["object_type"] == "administrativedivision"
    assert results[0]["name"]["fi"] == "Turku"
