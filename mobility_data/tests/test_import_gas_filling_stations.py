import pytest

from mobility_data.models import ContentType, MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_importer():
    import_command("import_gas_filling_stations", test_mode="gas_filling_stations.json")
    assert (
        ContentType.objects.filter(type_name=ContentType.GAS_FILLING_STATION).count()
        == 1
    )
    assert (
        MobileUnit.objects.filter(
            content_type__type_name=ContentType.GAS_FILLING_STATION
        ).count()
        == 2
    )
    assert MobileUnit.objects.get(name="Raisio Kuninkoja")
    unit = MobileUnit.objects.get(name="Turku Satama")
    assert unit
    assert unit.address == "Tuontiväylä 42 abc 1-2, 20200 Turku"
    # Transform to source data srid
    unit.geometry.transform(3857)
    assert pytest.approx(unit.geometry.x, 0.0000000001) == 2472735.3962113541
    assert unit.extra["operator"] == "Gasum"
