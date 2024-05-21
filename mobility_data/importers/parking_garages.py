import csv
import logging

from django.conf import settings
from django.contrib.gis.geos import Point
from munigeo.models import Municipality

from .utils import (
    get_full_csv_file_name,
    get_municipality_name,
    get_street_name_translations,
    LANGUAGES,
    MobileUnitDataBase,
    split_string_at_first_digit,
)

logger = logging.getLogger("mobility_data")
SOURCE_DATA_SRID = 3877

CONTENT_TYPE_NAME = "ParkingGarage"
SOURCE_DATA_FILE_NAME = "parkkihallit.csv"
COLUMN_MAPPINGS = {
    "name": 0,
    "address": 1,
    "N": 2,
    "E": 3,
    "parking_spaces": 4,
    "disabled_spaces": 5,
    "charging_stations": 6,
    "services_fi": 7,
    "services_sv": 8,
    "services_en": 9,
    "notes_fi": 10,
    "notes_sv": 11,
    "notes_en": 12,
}


class ParkingGarage(MobileUnitDataBase):

    def __init__(self, values):
        super().__init__()
        x = float(values[COLUMN_MAPPINGS["E"]])
        y = float(values[COLUMN_MAPPINGS["N"]])
        self.geometry = Point(x, y, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        try:
            self.municipality = Municipality.objects.get(
                name=get_municipality_name(self.geometry)
            )
        except Municipality.DoesNotExist:
            self.municipality = None
        address = values[COLUMN_MAPPINGS["address"]]
        street_name, street_number = split_string_at_first_digit(address)
        # As the source data contains only Finnish street names, we need to get the translations
        translated_street_names = get_street_name_translations(
            street_name.strip(), self.municipality
        )
        self.extra["services"] = {}
        self.extra["notes"] = {}
        for lang in LANGUAGES:
            self.name[lang] = values[COLUMN_MAPPINGS["name"]]
            self.address[lang] = f"{translated_street_names[lang]} {street_number}"
            self.extra["services"][lang] = values[COLUMN_MAPPINGS[f"services_{lang}"]]
            self.extra["notes"][lang] = values[COLUMN_MAPPINGS[f"notes_{lang}"]]

        try:
            parking_spaces = int(values[COLUMN_MAPPINGS["parking_spaces"]])
        except ValueError:
            parking_spaces = None
        self.extra["parking_spaces"] = parking_spaces

        try:
            disabled_spaces = int(values[COLUMN_MAPPINGS["disabled_spaces"]])
        except ValueError:
            disabled_spaces = None
        self.extra["disabled_spaces"] = disabled_spaces
        self.extra["charging_stations"] = values[COLUMN_MAPPINGS["charging_stations"]]


def get_parking_garage_objects():
    file_name = get_full_csv_file_name(SOURCE_DATA_FILE_NAME, CONTENT_TYPE_NAME)
    parking_garages = []
    with open(file_name, encoding="utf-8-sig") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        for i, row in enumerate(csv_reader):
            # Discard header row
            if i > 0:
                parking_garages.append(ParkingGarage(row))

    return parking_garages
