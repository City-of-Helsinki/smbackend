from io import StringIO

import pytest
from django.core.management import call_command

from mobility_data.models import MobileUnit


def import_command(*args, **kwargs):
    out = StringIO()
    call_command(
        "import_bicycle_stands",
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
    return out.getvalue()


@pytest.mark.django_db
def test_importer(
    municipality,
    administrative_division_type,
    administrative_division,
    administrative_division_geometry,
    streets,
    address,
):
    import_command(test_mode="bicycle_stands.xml")
    assert MobileUnit.objects.all().count() == 3
    # <GIS:Id>0</GIS:Id> in fixture xml.
    stand_normal = MobileUnit.objects.all()[0]
    # <GIS:Id>182213917</GIS:Id> in fixture xml.
    stand_covered_hull_lockable = MobileUnit.objects.all()[1]
    # <GIS:Id>319490982</GIS:Id> in fixture xml
    stand_external = MobileUnit.objects.all()[2]
    assert stand_normal.name_fi == "Linnanpuisto"
    assert stand_normal.name_sv == "Slottsparken"
    extra = stand_normal.extra
    assert extra["model"] == "Normaali"
    assert extra["maintained_by_turku"] is True
    assert extra["covered"] is False
    assert extra["hull_lockable"] is False
    assert extra["number_of_places"] == 24
    assert extra["number_of_stands"] == 2
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
    # and address number is assigned as name and that is "Test Street 42".
    assert stand_external.name == "Test Street 42"
    assert stand_external.name_sv == "Test StreetSV 42"
    extra = stand_external.extra
    assert extra["maintained_by_turku"] is False
    # As there are no info for stand that are not maintained by turku
    # field are set to None.
    assert extra["covered"] is None
    assert extra["hull_lockable"] is None
    assert extra["number_of_places"] is None
    assert extra["number_of_stands"] is None
