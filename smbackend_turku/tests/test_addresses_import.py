import logging
import math

import pytest
from munigeo.models import Address, get_default_srid

from smbackend_turku.importers.addresses import AddressImporter
from smbackend_turku.tests.utils import create_municipality, get_location


@pytest.mark.django_db
def test_address_import():
    logger = logging.getLogger(__name__)

    # Create Turku municipality
    create_municipality()

    address_importer = AddressImporter(logger=logger)
    address_importer.data_path = "smbackend_turku/tests/data"
    address_importer.import_addresses()

    addresses = Address.objects.count()
    address_1 = Address.objects.get(id=1)
    address_2 = Address.objects.get(id=2)

    address_1_location = get_location(23461366, 6705247, get_default_srid())
    address_2_location = get_location(23459033, 6702623, get_default_srid())

    assert addresses == 2
    assert address_1.street.name == "Kuuvuorenkatu"
    assert address_2.street.name == "Valtaojantie"
    assert address_1.number == "15"
    assert address_2.number == "26"
    assert math.isclose(address_1.location.x, address_1_location.x, rel_tol=1e-6)
    assert math.isclose(address_1.location.y, address_1_location.y, rel_tol=1e-6)
    assert math.isclose(address_2.location.x, address_2_location.x, rel_tol=1e-6)
    assert math.isclose(address_2.location.y, address_2_location.y, rel_tol=1e-6)
