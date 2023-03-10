import pytest
from munigeo.models import Municipality

from mobility_data.importers.loading_unloading_places import CONTENT_TYPE_NAME
from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
@pytest.mark.django_db
def test_import(municipalities):
    import_command(
        "import_loading_and_unloading_places",
        test_mode="loading_and_unloading_places.geojson",
    )
    assert ContentType.objects.all().count() == 1
    assert MobileUnit.objects.all().count() == 3
    turku_muni = None
    try:
        turku_muni = Municipality.objects.get(name="Turku")
    except Municipality.DoesNotExist:
        assert turku_muni
    lantinen_rantakatu = MobileUnit.objects.get(name="Läntinen Rantakatu")
    assert lantinen_rantakatu.content_types.all().count() == 1
    assert lantinen_rantakatu.content_types.first().name == CONTENT_TYPE_NAME
    assert lantinen_rantakatu.name_sv == "Östra Strandgatan"
    assert lantinen_rantakatu.name_en == "Läntinen Rantakatu"
    assert lantinen_rantakatu.address_fi == "Läntinen Rantakatu 13"
    assert lantinen_rantakatu.address_sv == "Östra Strandgatan 13"
    assert lantinen_rantakatu.address_en == "Läntinen Rantakatu 13"
    assert lantinen_rantakatu.address_zip == "20700"
    assert lantinen_rantakatu.municipality == turku_muni

    assert lantinen_rantakatu.extra["lastauspiste"]["fi"] == "Lastausalue"
    assert lantinen_rantakatu.extra["lastauspiste"]["sv"] == "Lastningsplats"
    assert lantinen_rantakatu.extra["lastauspiste"]["en"] == "Loading zone"

    assert lantinen_rantakatu.extra["Saavutettavuus"]["fi"] == "Kadunvarsipysäköinti"
    assert lantinen_rantakatu.extra["Saavutettavuus"]["sv"] == "Parkering på gata"
    assert lantinen_rantakatu.extra["Saavutettavuus"]["en"] == "On-street parking"

    assert lantinen_rantakatu.extra["rajoitustyyppi"]["fi"] == "Erityisalue"
    assert lantinen_rantakatu.extra["rajoitustyyppi"]["sv"] == "Specialområde"
    assert lantinen_rantakatu.extra["rajoitustyyppi"]["en"] == "Special area"

    assert lantinen_rantakatu.extra["paikkoja_y"] == 2
