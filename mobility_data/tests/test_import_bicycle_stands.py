import pytest

from mobility_data.models import MobileUnit

from .utils import import_command


@pytest.mark.django_db
def test_geojson_import(
    municipalities,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    import_command(
        "import_bicycle_stands", test_mode="bicycle_stands_for_units.geojson"
    )
    assert MobileUnit.objects.all().count() == 3
    kupittaan_maauimala = MobileUnit.objects.get(name="Kupittaan maauimala")
    assert kupittaan_maauimala
    kupittaan_palloiluhalli = MobileUnit.objects.get(name="Kupittaan palloiluhalli")
    assert kupittaan_palloiluhalli
    turun_amk = MobileUnit.objects.get(name="Turun AMK")
    assert turun_amk
    assert kupittaan_maauimala.extra["hull_lockable"] is False
    assert kupittaan_maauimala.extra["covered"] is False
    assert kupittaan_maauimala.extra["number_of_stands"] == 35
    assert kupittaan_maauimala.extra["number_of_places"] == 140
    assert kupittaan_maauimala.address_fi == "Kupittaankatu 8"
    assert kupittaan_maauimala.address_sv == "Kuppisgatan 8"
    assert kupittaan_palloiluhalli.extra["hull_lockable"] is True
    assert kupittaan_palloiluhalli.extra["covered"] is True
    assert turun_amk.extra["hull_lockable"] is True
    assert turun_amk.extra["covered"] is False
    assert turun_amk.municipality.name == "Turku"


@pytest.mark.django_db
def test_wfs_importer(
    municipalities,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    import_command("import_bicycle_stands", test_mode="bicycle_stands.gml")
    assert MobileUnit.objects.all().count() == 3
    # <GIS:Id>0</GIS:Id> in fixture xml.
    stand_normal = MobileUnit.objects.all()[0]
    # <GIS:Id>182213917</GIS:Id> in fixture xml.
    stand_covered_hull_lockable = MobileUnit.objects.all()[1]
    # <GIS:Id>319490982</GIS:Id> in fixture xml
    stand_external = MobileUnit.objects.all()[2]
    assert stand_normal.name_fi == "Linnanpuisto"
    assert stand_normal.name_sv == "Slottsparken"
    assert stand_normal.municipality.name == "Turku"
    extra = stand_normal.extra
    assert extra["model"] == "Normaali"
    assert extra["maintained_by_turku"] is True
    assert extra["covered"] is False
    assert extra["hull_lockable"] is False
    assert extra["number_of_places"] == 24
    assert extra["number_of_stands"] == 2
    assert stand_covered_hull_lockable.name == "Pitkäpellonkatu 7"
    assert stand_covered_hull_lockable.name_sv == "Långåkersgatan 7"
    extra = stand_covered_hull_lockable.extra
    assert extra["maintained_by_turku"] is True
    assert extra["covered"] is True
    assert extra["hull_lockable"] is True
    assert extra["number_of_places"] == 18
    assert extra["number_of_stands"] == 1
    # external stand has no street name, so the closest street name
    # and address number is assigned as name and that is "Kupittaankatu 8".
    assert stand_external.name == "Kupittaankatu 8"
    assert stand_external.name_sv == "Kuppisgatan 8"
    extra = stand_external.extra
    assert extra["maintained_by_turku"] is False
    # As there are no info for stand that are not maintained by turku
    # field are set to None.
    assert extra["covered"] is None
    assert extra["hull_lockable"] is None
    assert extra["number_of_places"] is None
    assert extra["number_of_stands"] is None
