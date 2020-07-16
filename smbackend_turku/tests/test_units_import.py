import math
import pytest
import logging

from unittest.mock import patch
from services.models import Unit, UnitConnection

from smbackend_turku.tests.utils import get_test_resource, get_location, get_opening_hours, create_municipality


@pytest.mark.django_db
@patch("smbackend_turku.importers.utils.get_turku_resource")
def test_unit_import(resource):
    from smbackend_turku.importers.units import UnitImporter

    logger = logging.getLogger(__name__)
    unit_importer = UnitImporter(logger=logger)

    # Create Turku municipality
    create_municipality()

    resource.return_value = get_test_resource()
    unit_importer.import_units()

    units = Unit.objects.count()
    unit_1 = Unit.objects.get(id=740)
    unit_2 = Unit.objects.get(id=967)

    assert units == 2
    assert unit_1.name == "Terapia"
    assert unit_2.name == "Päiväkoti"
    assert unit_2.email == "testi.15@turku.fi"

    unit_1_location = get_location(22.2740709, 60.4378786, 4326)
    unit_2_location = get_location(22.3210619, 60.4722408, 4326)

    assert math.isclose(unit_1.location.x, unit_1_location.x, rel_tol=1e-6)
    assert math.isclose(unit_1.location.y, unit_1_location.y, rel_tol=1e-6)
    assert math.isclose(unit_2.location.x, unit_2_location.x, rel_tol=1e-6)
    assert math.isclose(unit_2.location.y, unit_2_location.y, rel_tol=1e-6)

    assert unit_1.municipality_id == "turku"
    assert unit_2.municipality.id == "turku"
    assert unit_1.address_postal_full.replace(u"\xa0", " ") == "Testitie 2 20810 Turku"
    assert unit_2.address_postal_full.replace(u"\xa0", " ") == "Testikatu 21 20540 Turku"
    assert unit_1.street_address == "Testitie 2"
    assert unit_2.street_address == "Testikatu 21"
    assert unit_1.address_zip == "20810"
    assert unit_2.address_zip == "20540"

    assert unit_1.identifiers.first().value == "8j76h2hj-hb8b-8j87-j7g7-8796hg87654k"
    assert unit_2.identifiers.first().value == "hs8790h7-h898-97h7-s9kj-86597867g978"

    OPENING_HOURS_SECTION_TYPE = 5
    unit_connections_opening_hours = UnitConnection.objects.filter(section_type=OPENING_HOURS_SECTION_TYPE).count()
    unit_connection_1 = UnitConnection.objects.get(unit=unit_1, section_type=OPENING_HOURS_SECTION_TYPE)
    unit_connection_2 = UnitConnection.objects.get(unit=unit_2, section_type=OPENING_HOURS_SECTION_TYPE)

    opening_hours_1 = get_opening_hours("08:00:00", "15:00:00", "1-5")
    opening_hours_2 = get_opening_hours("06:30:00", "17:00:00", "1-5")

    opening_hours_name_1 = '{} {}'.format('<b>Aukioloajat</b>', opening_hours_1)
    opening_hours_name_2 = '{} {}'.format('<b>Avoinna</b>', opening_hours_2)

    assert unit_connections_opening_hours == 2
    assert unit_connection_1.name == opening_hours_name_1
    assert unit_connection_2.name == opening_hours_name_2
