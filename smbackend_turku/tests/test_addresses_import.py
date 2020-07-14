import logging
from django.test import TestCase
from django.conf import settings

from munigeo.models import Address, Municipality
from django.contrib.gis.geos import Point

from smbackend_turku.importers.addresses import AddressImporter


class AddressImportTestCase(TestCase):

    logger = logging.getLogger(__name__)

    def setUp(self):
        Municipality.objects.create(id='turku', name='Turku', name_fi='Turku', name_sv='Åbo')

    def test_address_import(self):

        address_importer = AddressImporter(logger=self.logger)
        address_importer.data_path = 'smbackend_turku/tests/data'
        address_importer.import_addresses()

        addresses_on_db = Address.objects.all()

        address_1 = Address.objects.get(id=1)
        address_2 = Address.objects.get(id=2)

        address_1_location = Point(srid=3877, x=float(23461366), y=float(6705247))
        address_2_location = Point(srid=3877, x=float(23459033), y=float(6702623))

        address_1_location.transform(settings.DEFAULT_SRID)
        address_2_location.transform(settings.DEFAULT_SRID)

        self.assertEqual(len(addresses_on_db), 2)
        self.assertEqual(address_1.street.name, 'Kuuvuorenkatu')
        self.assertEqual(address_2.street.name, 'Valtaojantie')
        self.assertEqual(address_1.number, '15')
        self.assertEqual(address_2.number, '26')
        self.assertEqual(address_1.location.x, address_1_location.x)
        self.assertEqual(address_1.location.y, address_1_location.y)
        self.assertEqual(address_2.location.x, address_2_location.x)
        self.assertEqual(address_2.location.y, address_2_location.y)
