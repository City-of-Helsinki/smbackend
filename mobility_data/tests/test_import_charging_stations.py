import pytest
from munigeo.models import Address

from mobility_data.importers.charging_stations import CONTENT_TYPE_NAME
from mobility_data.models import ContentType, MobileUnit
from smbackend_turku.importers.constants import CHARGING_STATION_SERVICE_NAMES

from .utils import import_command


@pytest.mark.django_db
def test_import_charging_stations(
    municipalities,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    import_command("import_charging_stations", test_mode="charging_stations.csv")
    assert ContentType.objects.filter(name=CONTENT_TYPE_NAME).count() == 1
    assert MobileUnit.objects.filter(content_type__name=CONTENT_TYPE_NAME).count() == 3
    aimopark = MobileUnit.objects.get(name="Aimopark, Yliopistonkatu 29")
    assert aimopark.address == "Yliopistonkatu 29"
    assert aimopark.address_sv == "Universitetsgatan 29"
    assert aimopark.address_en == "Yliopistonkatu 29"
    yliopistonkatu_29 = Address.objects.get(full_name_fi="Yliopistonkatu 29")
    assert (
        aimopark.geometry.equals_exact(yliopistonkatu_29.location, tolerance=70) is True
    )
    chargers = aimopark.extra["chargers"]
    assert len(chargers) == 2
    assert chargers[0]["plug"] == "Type 2"
    assert chargers[0]["power"] == "22"
    assert chargers[0]["number"] == "2"
    assert aimopark.extra["payment"] == "Sisältyy hintaan"
    assert aimopark.extra["charge_target"] == "Julkinen"
    assert aimopark.extra["method_of_use"] == "P-paikan hintaan"
    turku_energia = MobileUnit.objects.get(name="Turku Energia, Aninkaistenkatu 20")
    assert turku_energia.extra["administrator"]["fi"] == "Turku Energia"
    assert turku_energia.extra["administrator"]["sv"] == "Åbo Energi"
    assert turku_energia.extra["administrator"]["en"] == "Turku Energia"
    # Test that charging station without administrator gets the name from service
    name = f"{CHARGING_STATION_SERVICE_NAMES['fi']}, Ratapihankatu 53"
    ratapihankatu = MobileUnit.objects.get(name=name)
    assert ratapihankatu
    assert (
        ratapihankatu.name_sv
        == f"{CHARGING_STATION_SERVICE_NAMES['sv']}, Bangårdsgatan 53"
    )
    assert (
        ratapihankatu.name_en
        == f"{CHARGING_STATION_SERVICE_NAMES['en']}, Ratapihankatu 53"
    )
