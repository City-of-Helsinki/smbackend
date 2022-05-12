import logging

import pytest
from munigeo.models import Address, PostalCodeArea, Street

from smbackend_turku.importers.addresses import AddressImporter, SOURCE_DATA_SRID
from smbackend_turku.tests.utils import (
    create_municipalities,
    get_location,
    get_test_addresses_layer,
)


@pytest.mark.django_db
def test_address_import():
    logger = logging.getLogger(__name__)

    # Create Turku, Kaarina municipalities
    create_municipalities()
    address_importer = AddressImporter(logger=logger, layer=get_test_addresses_layer())
    address_importer.import_addresses()
    assert Address.objects.count() == 3
    assert Street.objects.count() == 3
    assert PostalCodeArea.objects.count() == 2
    postal_code_areas = PostalCodeArea.objects.all()
    postal_code_areas[0].postal_code == "20320"
    postal_code_areas[1].postal_code == "21620"
    streets = Street.objects.all()
    # Test street without swedish name, should get the finnish name
    assert streets[0].name_fi == "Rauhalankalliontie"
    assert streets[0].name_sv == "Rauhalankalliontie"

    assert streets[1].name_fi == "Unikkopolku"
    assert streets[1].name_sv == "Vallmostigen"
    addresses = Address.objects.all()
    addr_rauhalankalliontie = addresses[0]
    assert addr_rauhalankalliontie.number == "3"
    assert addr_rauhalankalliontie.number_end == ""
    assert addr_rauhalankalliontie.letter == ""
    assert addr_rauhalankalliontie.postal_code_area.postal_code == "21620"
    # test 1-4 number
    addr_unikkopolku = addresses[1]
    assert addr_unikkopolku.number == "1"
    assert addr_unikkopolku.number_end == "4"
    assert addr_unikkopolku.postal_code_area.postal_code == "20320"
    # test letter after number
    addr_koppelonkatu = addresses[2]
    addr_koppelonkatu.number == "13"
    addr_koppelonkatu.letter == "b"
    location = get_location(23464210.875, 6703317.030, SOURCE_DATA_SRID)
    assert addr_koppelonkatu.location == location
