from unittest.mock import patch

import pytest

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_or_create_content_type_from_config,
    save_to_database,
)
from mobility_data.models import MobileUnit

from .utils import get_test_fixture_data_source


def get_geojson_data_source(file_name):
    ds = get_test_fixture_data_source(file_name)
    return [("geojson", ds)]


def get_gml_data_source(file_name):
    ds = get_test_fixture_data_source(file_name)
    return [("gml", ds)]


@pytest.mark.django_db
@patch("mobility_data.importers.bicycle_stands.get_data_sources")
def test_geojson_import(
    get_data_sources_mock,
    municipalities,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    from mobility_data.importers.bicycle_stands import (
        CONTENT_TYPE_NAME,
        get_bicycle_stand_objects,
    )

    get_data_sources_mock.return_value = get_geojson_data_source(
        "bicycle_stands_for_units.geojson"
    )
    objects = get_bicycle_stand_objects()
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 3
    assert num_deleted == 0
    assert MobileUnit.objects.all().count() == 3
    kupittaan_maauimala = MobileUnit.objects.get(
        name="Pyöräpysäköinti Kupittaan maauimala"
    )
    assert kupittaan_maauimala
    kupittaan_palloiluhalli = MobileUnit.objects.get(
        name="Pyöräpysäköinti Kupittaan palloiluhalli"
    )
    assert kupittaan_palloiluhalli
    turun_amk = MobileUnit.objects.get(name="Pyöräpysäköinti Turun AMK")
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
    delete_mobile_units(content_type)
    assert (
        MobileUnit.objects.filter(content_types__type_name=CONTENT_TYPE_NAME).count()
        == 0
    )


@pytest.mark.django_db
@patch("mobility_data.importers.bicycle_stands.get_data_sources")
def test_gml_importer(
    get_data_sources_mock,
    municipalities,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    from mobility_data.importers.bicycle_stands import (
        CONTENT_TYPE_NAME,
        get_bicycle_stand_objects,
    )

    get_data_sources_mock.return_value = get_gml_data_source("bicycle_stands.gml")
    objects = get_bicycle_stand_objects()
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 3
    assert num_deleted == 0
    assert MobileUnit.objects.all().count() == 3
    # <GIS:Id>0</GIS:Id> in fixture xml.
    stand_normal = MobileUnit.objects.first()
    # <GIS:Id>182213917</GIS:Id> in fixture xml.
    stand_covered_hull_lockable = MobileUnit.objects.all()[1]
    # <GIS:Id>319490982</GIS:Id> in fixture xml
    stand_external = MobileUnit.objects.all()[2]
    assert stand_normal.name_fi == "Pyöräpysäköinti Linnanpuisto"
    assert stand_normal.name_sv == "Cykelparkering Slottsparken"
    assert stand_normal.name_en == "Bicycle parking Linnanpuisto"
    assert stand_normal.municipality.name == "Turku"
    extra = stand_normal.extra
    assert extra["model"] == "Normaali"
    assert extra["maintained_by_turku"] is True
    assert extra["covered"] is False
    assert extra["hull_lockable"] is False
    assert extra["number_of_places"] == 24
    assert extra["number_of_stands"] is None
    assert stand_covered_hull_lockable.name == "Pyöräpysäköinti Pitkäpellonkatu 7"
    assert stand_covered_hull_lockable.name_sv == "Cykelparkering Långåkersgatan 7"
    extra = stand_covered_hull_lockable.extra
    assert extra["maintained_by_turku"] is True
    assert extra["covered"] is True
    assert extra["hull_lockable"] is True
    assert extra["number_of_places"] == 18
    assert extra["number_of_stands"] is None
    # external stand has no street name, so the closest street name
    # and address number is assigned as name and that is "Kupittaankatu 8".
    assert stand_external.name == "Pyöräpysäköinti Kupittaankatu 8"
    assert stand_external.name_sv == "Cykelparkering Kuppisgatan 8"
    extra = stand_external.extra
    assert extra["maintained_by_turku"] is False
    # As there are no info for stand that are not maintained by turku
    # field are set to None.
    assert extra["covered"] is None
    assert extra["hull_lockable"] is None
    assert extra["number_of_places"] is None
    assert extra["number_of_stands"] is None
