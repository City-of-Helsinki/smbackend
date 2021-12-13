from io import StringIO
import pytest
from django.core.management import call_command
from .fixtures import *
from mobility_data.models import (
    MobileUnit,
)

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
    streets,
    address
):    
    out = import_command(test_mode="bicycle_stands.xml")  
    assert MobileUnit.objects.all().count() == 3
    # <GIS:Id>0</GIS:Id> in fixture xml.
    stand_normal = MobileUnit.objects.all()[0]
    # <GIS:Id>182213917</GIS:Id> in fixture xml.
    stand_covered_hull_lockable = MobileUnit.objects.all()[1]  
    # <GIS:Id>319490982</GIS:Id> in fixture xml
    stand_external = MobileUnit.objects.all()[2]

    assert stand_normal.name_fi == "Linnanpuisto"
    assert stand_normal.name_sv == "LinnanpuistoSV"
    assert stand_normal.name_en == "Linnanpuisto"  
    extra = stand_normal.extra
    assert extra["model"] == "Normaali"
    assert extra["maintained_by_turku"] == True
    assert extra["covered"] == False
    assert extra["hull_lockable"] == False
    assert extra["number_of_places"] == 24
    assert extra["number_of_stands"] == 2
    assert extra["number_of_stands"] == 2
    
    assert stand_covered_hull_lockable.name == "Pitkäpellonkatu"
    extra = stand_covered_hull_lockable.extra
    assert extra["maintained_by_turku"] == True
    assert extra["covered"] == True
    assert extra["hull_lockable"] == True
    assert extra["number_of_places"] == 18
    assert extra["number_of_stands"] == 1
    # external stand has no street name, so the closes street name 
    # is "Test Street".
    assert stand_external.name == "Test Street"
    extra = stand_external.extra    
    assert extra["maintained_by_turku"] == False
    # As there are no info for stand that are not maintained by turku
    # field are set to None.
    assert extra["covered"] == None
    assert extra["hull_lockable"] == None
    assert extra["number_of_places"] == None
    assert extra["number_of_stands"] == None
