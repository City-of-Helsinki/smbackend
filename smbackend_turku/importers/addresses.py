import csv
import os

from django.conf import settings
from django.contrib.gis.geos import Point
from munigeo.models import Address, Municipality, Street


class AddressImporter:
    def __init__(self, logger):
        self.logger = logger

        if hasattr(settings, 'PROJECT_ROOT'):
            root_dir = settings.PROJECT_ROOT
        else:
            root_dir = settings.BASE_DIR
        self.data_path = os.path.join(root_dir, 'data')

        self.csv_field_names = ('municipality', 'street', 'street_number', 'y', 'x')
        self.valid_municipalities = ['turku', 'åbo']

    def _import_address(self, entry):
        street, _ = Street.objects.get_or_create(**entry['street'])
        location = Point(
            srid=3877,
            **entry['point']
        )

        Address.objects.get_or_create(
            street=street,
            defaults={'location': location},
            **entry['address']
        )

    def _create_address_mapping(self, address_reader):
        turku = Municipality.objects.get(id='turku')
        multi_lingual_addresses = {}
        for row in address_reader:
            if row['municipality'].lower() not in self.valid_municipalities:
                continue

            coordinates = row['y'] + row['x']
            if coordinates not in multi_lingual_addresses:
                multi_lingual_addresses[coordinates] = {
                    'street': {
                        'municipality': turku,
                    },
                    'point': {
                        'x': float(row['x']),
                        'y': float(row['y']),
                    },
                    'address': {
                        'number': row['street_number'],
                    }
                }

            if row['municipality'].lower() == 'turku':
                multi_lingual_addresses[coordinates]['street']['name_fi'] = row['street']
            elif row['municipality'].lower() == 'åbo':
                # If we don't have a Finnish name for the street, use the Swedish name
                # for the Finnish street name as well since that is most likely an
                # expected value. If there is a Finnish name for the coordinates lower
                # down in the coordinate list then the Finnish name will be overridden.
                if 'name_fi' not in multi_lingual_addresses[coordinates]['street']:
                    multi_lingual_addresses[coordinates]['street']['name_fi'] = row['street']
                multi_lingual_addresses[coordinates]['street']['name_sv'] = row['street']
        return multi_lingual_addresses

    def import_addresses(self):
        file_path = os.path.join(self.data_path, 'turku_addresses.csv')
        entries_created = 0

        Street.objects.all().delete()
        Address.objects.all().delete()

        with open(file_path, encoding='latin-1') as csvfile:
            address_reader = csv.DictReader(csvfile, delimiter=';', fieldnames=self.csv_field_names)
            multi_lingual_addresses = self._create_address_mapping(address_reader)

            for entry in multi_lingual_addresses.values():
                self._import_address(entry)
                entries_created += 1
                if entries_created % 1000 == 0:
                    self.logger.debug('row {} / {}'.format(entries_created, len(multi_lingual_addresses.values())))
        self.logger.debug("Added {} addresses".format(entries_created))


def import_addresses(**kwargs):
    importer = AddressImporter(**kwargs)
    return importer.import_addresses()
