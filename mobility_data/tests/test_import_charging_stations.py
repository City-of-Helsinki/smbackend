import pytest

from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_importer(
    municipality,
    administrative_division_type,
    administrative_division,
    streets,
    address,
):
    import_command("import_charging_stations", test_mode="charging_stations.json")
    assert (
        ContentType.objects.filter(type_name=ContentType.CHARGING_STATION).count() == 1
    )
    assert (
        MobileUnit.objects.filter(
            content_type__type_name=ContentType.CHARGING_STATION
        ).count()
        == 2
    )
    unit = MobileUnit.objects.get(name="AimoPark Stockmann Turku")
    assert unit.address_fi == "Kristiinankatu 11, 20100 Turku"
    assert unit.address_sv == "Kristinegatan 11, 20100 Turku"
    unit = MobileUnit.objects.get(name="Hotel Kakola")
    assert unit
    # Transform to source data srid
    unit.geometry.transform(4326)
    assert pytest.approx(unit.geometry.x, 0.0001) == 22.247
    assert unit.extra["url"] == "https://latauskartta.fi/latauspiste/2629/Hotel+Kakola/"
