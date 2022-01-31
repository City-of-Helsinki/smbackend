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
    url = reverse("search") + "?q=museo&use_trigram=false"
    response = api_client.get(url)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results["units"]) == 2
    assert len(results["services"]) == 1
    assert len(results["addresses"]) == 0
    assert len(results["administrative_divisions"]) == 0
    # Test that unit Impivaara is retrieved from service Uimahalli
    url = reverse("search") + "?q=uimahalli&use_trigram=false"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results["units"][0]["name"]["fi"] == "Impivaara"
    assert results["services"][0]["name"]["fi"] == "Uimahalli"
    # Test address search
    url = reverse("search") + "?q=kurra&use_trigram=false"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results["addresses"][0]["full_name"]["fi"] == "Kurrapolku 1A"
    # Test administrative division search
    url = reverse("search") + "?q=tur&use_trigram=false"
    response = api_client.get(url)
    results = response.json()["results"]
    assert results["administrative_divisions"][0]["name"]["fi"] == "Turku"
