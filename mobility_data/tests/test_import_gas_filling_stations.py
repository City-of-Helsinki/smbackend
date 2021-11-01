from io import StringIO
import pytest
from django.core.management import call_command
from mobility_data.models import (
    MobileUnit,
    ContentType,
    GasFillingStationContent,   
)

def import_command(*args, **kwargs):
        out = StringIO()
        call_command(
            "import_gas_filling_stations",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

@pytest.mark.django_db
def test_importer():
    out = import_command(test_mode="gas_filling_stations.json")
    assert ContentType.objects.filter(type_name=ContentType.GAS_FILLING_STATION).count() == 1
    assert MobileUnit.objects.filter(content_type__type_name=ContentType.GAS_FILLING_STATION).count() == 2
    assert MobileUnit.objects.get(name="Raisio Kuninkoja")
    unit = MobileUnit.objects.get(name="Turku Satama")
    assert unit
    # Transform to source data srid
    unit.geometry.transform(3857)
    assert pytest.approx(unit.geometry.x, 0.0000000001) ==  2472735.3962113541
    assert GasFillingStationContent.objects.all().count() == 2  
    content = GasFillingStationContent.objects.get(mobile_unit__name="Turku Satama") 
    assert content.operator == "Gasum"
    assert content.mobile_unit == unit
