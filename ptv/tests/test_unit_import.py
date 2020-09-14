import datetime

import pytest

from ptv.models import ServicePTVIdentifier, UnitPTVIdentifier
from ptv.tests.utils import create_municipality, get_ptv_test_resource
from services.models import Unit, UnitConnection, UnitIdentifier


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


@pytest.mark.django_db
def test_unit_syncher_finish():
    """
    Make sure unit_syncher.finish() removes only the units that are no longer in the source data of the
    selected municipality.
    """
    from ptv.importers.ptv_units import UnitPTVImporter

    create_municipality()

    unit_importer = UnitPTVImporter(area_code="001")
    data = get_ptv_test_resource()
    unit_importer._import_units(data)
    unit_importer.unit_syncher.finish()
    assert Unit.objects.get(name="Terveysasema")
    assert Unit.objects.get(name="Peruskoulu")

    # Import data from other municipality
    unit_importer = UnitPTVImporter(area_code="003")
    data = get_ptv_test_resource(resource_name="channel_3")
    unit_importer._import_units(data)
    unit_importer.unit_syncher.finish()
    assert Unit.objects.get(name="Terveyskeskus")

    assert Unit.objects.count() == 3

    # Import data from the first municipality, but now one unit is no longer in the source
    unit_importer = UnitPTVImporter(area_code="001")
    data = get_ptv_test_resource(resource_name="channel_2")
    unit_importer._import_units(data)
    unit_importer.unit_syncher.finish()

    assert Unit.objects.count() == 2
    assert Unit.objects.get(name="Terveysasema")
    assert Unit.objects.get(name="Terveyskeskus")
    assert not Unit.objects.filter(name="Peruskoulu").exists()


@pytest.mark.django_db
def test_skip_units_from_another_source():
    create_municipality()
    modified_time = datetime.datetime(
        year=2020,
        month=1,
        day=1,
        hour=1,
        minute=1,
        second=1,
        tzinfo=datetime.timezone.utc,
    )

    # Unit imported from another source
    unit = Unit.objects.create(id=777, last_modified_time=modified_time)
    unit_ptv_id = "0001a1c4-6273-424f-8d17-2ac62be89741"
    UnitIdentifier.objects.create(namespace="ptv", value=unit_ptv_id, unit=unit)

    # Unit imported from PTV
    ptv_unit = Unit.objects.create(
        id=778, last_modified_time=modified_time, data_source="PTV"
    )
    ptv_unit_ptv_id = "00006fe3-7df2-409e-9cd6-cce4bf4338b1"
    UnitIdentifier.objects.create(namespace="ptv", value=ptv_unit_ptv_id, unit=ptv_unit)
    UnitPTVIdentifier.objects.create(
        id=ptv_unit_ptv_id, unit=ptv_unit, source_municipality=1
    )

    assert Unit.objects.count() == 2

    from ptv.importers.ptv_units import UnitPTVImporter

    unit_importer = UnitPTVImporter(area_code="001")
    data = get_ptv_test_resource()
    unit_importer._import_units(data)
    unit_importer.unit_syncher.finish()

    assert Unit.objects.count() == 2
    assert (
        Unit.objects.get(identifiers__value=unit_ptv_id).last_modified_time
        == modified_time
    )
    assert (
        Unit.objects.get(identifiers__value=ptv_unit_ptv_id).last_modified_time
        != modified_time
    )
