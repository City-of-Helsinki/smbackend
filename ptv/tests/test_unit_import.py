import pytest

from ptv.models import ServicePTVIdentifier
from ptv.tests.utils import create_municipality, get_ptv_test_resource
from services.models import Unit, UnitConnection


@pytest.mark.django_db
def test_unit_import():
    from ptv.importers.ptv_units import UnitPTVImporter

    unit_importer = UnitPTVImporter(area_code="001")
    municipality = create_municipality()

    data = get_ptv_test_resource()
    unit_importer._import_units(data)

    assert Unit.objects.count() == 2
    unit = Unit.objects.get(name="Terveysasema")

    assert unit.name_fi == "Terveysasema"
    assert unit.name_sv == "Hälsostationen"
    assert unit.description == "Terveysasema palvelee sairaustapauksissa."
    assert unit.email == "test-email@test.fi"
    assert unit.www == "https://www.testpage.fi"
    assert unit.identifiers.first().value == "0001a1c4-6273-424f-8d17-2ac62be89741"

    assert unit.municipality == municipality
    assert unit.street_address == "Testitie 13"
    assert unit.address_zip == "12345"

    assert UnitConnection.objects.count() == 3
    assert unit.connections.filter(section_type=1).first().email == "test-email@test.fi"
    assert unit.connections.filter(section_type=1).last().phone == "+358101010100"
    assert unit.connections.filter(section_type=1).last().name == "Asiakaspalvelu"
    assert (
        unit.connections.filter(section_type=5).first().name_fi
        == "Normaalit palveluajat\nKe 08:00-16:00\nPe 08:00-14:00"
    )

    assert ServicePTVIdentifier.objects.count() == 3
    assert ServicePTVIdentifier.objects.get(id="0008afc0-182c-4580-ba73-7472287f4d63")
