import pytest

from mobility_data.importers.share_car_parking_places import CONTENT_TYPE_NAME
from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_import_car_share_parking_places():
    import_command(
        "import_share_car_parking_places", test_mode="share_car_parking_places.geojson"
    )
    assert ContentType.objects.filter(type_name=CONTENT_TYPE_NAME).count() == 1
    assert MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count() == 3
    linnankatu = MobileUnit.objects.get(
        name="Yhteiskäyttöautojen pysäköintipaikka, Linnankatu 29"
    )
    assert linnankatu.name_sv == "Bilpoolbilars parkeringsplats, Slottsgatan 29"
    assert linnankatu.name_en == "Parking place for car sharing cars, Linnankatu 29"
    assert linnankatu.address_fi == "Linnankatu 29"
    assert linnankatu.address_sv == "Slottsgatan 29"
    assert linnankatu.address_en == "Linnankatu 29"
    assert linnankatu.extra["Rajoit_lis"]["fi"] == "Lisäkilpi: Ei koske P-tunnuksella"
    assert linnankatu.extra["Rajoit_lis"]["sv"] == "Gäller ej P-tecknet"
    assert linnankatu.extra["Rajoit_lis"]["en"] == "Z"
    assert linnankatu.extra["Kohde"] == "Linnankatu"
    assert linnankatu.extra["Saavutetta"] == "Vapaa pääsy"
    assert linnankatu.extra["Sähkölat"] is None
    assert linnankatu.extra["Paikkoja_y"] == "1"

    rautatientori = MobileUnit.objects.get(
        name="Yhteiskäyttöautojen pysäköintipaikka, Läntinen Pitkäkatu 26"
    )
    assert rautatientori.extra["Paikkoja_y"] == "2"
    rautatientori.extra["Invapaikko"] is None
