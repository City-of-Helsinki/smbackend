import csv
import logging

from django import db
from django.conf import settings
from django.contrib.gis.geos import Point

from mobility_data.models import ContentType, MobileUnit
from smbackend_turku.importers.constants import CHARGING_STATION_SERVICE_NAMES

# from smbackend_turku.importers.stations import ChargingStationImporter
from .utils import (
    delete_mobile_units,
    get_municipality_name,
    get_or_create_content_type,
    get_postal_code,
    get_street_name_translations,
    LANGUAGES,
    set_translated_field,
)

logger = logging.getLogger("mobility_data")

SOURCE_DATA_FILE_NAME = "LatauspisteetTurku.csv"
SOURCE_DATA_SRID = 3877
"""
Charging stations are indexed with this column, if multiple rows
has the same index, they contain multiple chargers.
"""
INDEX_COLUMN_NAME = "Latauspiste nro"
"""
Maps the source data column names. Key is the column name in source data,
value is name used internarly and set to the extra fields.
"""
COLUMN_NAME_MAPPINGS = {
    INDEX_COLUMN_NAME: "index",
    "Teho (kW)": "power",
    "Määrä": "number",
    "Pistoke": "plug",
    "X": "x",
    "Y": "y",
    "Osoite": "address",
    "Hallinnoija_fi": "administrator_fi",
    "Hallinnoija_sv": "administrator_sv",
    "Hallinnoija_en": "administrator_en",
    "Latauskohde": "charge_target",
    "Maksu": "payment",
    "Sähköhinta (€/kWh)": "electricity_price",
    "Tuntihinta (€/h)": "hour_price",
    "Käyttötapa": "method_of_use",
    "Tieto hankittu": "data_collected",
    "Tiedot päivitetty ": "data_updated",
    "Muuta": "other",
}


class ChargingStation:
    def __init__(self, values):
        self.is_active = True
        self.extra = {}
        self.extra["chargers"] = []
        self.extra["administrator"] = {}
        self.address = {}
        self.name = {}
        # Contains Only steet_name and number
        self.street_address = {}
        x = float(values["x"].replace(",", "."))
        y = float(values["y"].replace(",", "."))
        self.geometry = Point(x, y, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra["charge_target"] = values["charge_target"]
        self.extra["method_of_use"] = values["method_of_use"]
        self.extra["other"] = values["other"]
        self.extra["payment"] = values["payment"]
        self.municipality = get_municipality_name(self.geometry)
        self.zip_code = get_postal_code(self.geometry)
        tmp = values["address"].split(" ")
        address_number = None
        street_name = tmp[0]
        if len(tmp) > 1:
            address_number = tmp[1]
        translated_street_names = get_street_name_translations(
            street_name, self.municipality
        )
        for lang in LANGUAGES:
            self.address[lang] = translated_street_names[lang]
            self.extra["administrator"][lang] = values["administrator_%s" % lang]
            if address_number:
                self.address[lang] += f" {address_number}"
            if self.extra["administrator"][lang]:
                self.name[lang] = self.extra["administrator"][lang]
            else:
                self.name[lang] = CHARGING_STATION_SERVICE_NAMES[lang]
            self.name[lang] += f", {self.address[lang]}"

    def add_charger(self, values):
        charger = {}
        charger["power"] = values["power"]
        charger["number"] = values["number"]
        charger["plug"] = values["plug"]
        self.extra["chargers"].append(charger)


def get_number_of_rows(file_name):
    number_of_rows = None
    with open(file_name, encoding="utf-8-sig") as csv_file:
        number_of_rows = sum(1 for line in csv_file)
    return number_of_rows


def get_charging_station_objects(csv_file=None):
    # Store the imported stations to dict, the index is the key.
    charging_stations = {}

    if hasattr(settings, "PROJECT_ROOT"):
        root_dir = settings.PROJECT_ROOT
    else:
        root_dir = settings.BASE_DIR
    column_mappings = {}
    if not csv_file:
        file_name = f"{root_dir}/mobility_data/data/{SOURCE_DATA_FILE_NAME}"
    else:
        file_name = f"{root_dir}/mobility_data/tests/data/{csv_file}"
    number_of_rows = get_number_of_rows(file_name)

    with open(file_name, encoding="utf-8-sig") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                # Find the column index number for column names
                # This number is used when mapping the key value pairs.
                for i, key in enumerate(row):
                    if key in COLUMN_NAME_MAPPINGS:
                        column_name = COLUMN_NAME_MAPPINGS[key]
                        column_mappings[i] = column_name
                    else:
                        raise Exception(
                            "Unable to map column {}. Has the column name changed in the source data?".format(
                                key
                            )
                        )
            else:
                values = {}
                # Map the value of the row to the name of the column
                for i, value in enumerate(row):
                    key = column_mappings[i]
                    values[key] = value
                index = values["index"]
                if index not in charging_stations:
                    charging_station = ChargingStation(values)
                    charging_stations[index] = charging_station
                charging_stations[index].add_charger(values)
            line_count += 1
            if line_count >= number_of_rows - 1:
                break
    # create list from dict values.
    objects = [obj for obj in charging_stations.values()]
    return objects


@db.transaction.atomic
def delete_charging_stations():
    delete_mobile_units(ContentType.CHARGING_STATION)


@db.transaction.atomic
def create_charging_station_content_type():
    description = "Charging stations in province of SouthWest Finland."
    name = "Charging Station"
    content_type, _ = get_or_create_content_type(
        ContentType.CHARGING_STATION, name, description
    )
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_charging_stations()
    content_type = create_charging_station_content_type()

    for object in objects:
        is_active = object.is_active
        mobile_unit = MobileUnit.objects.create(
            is_active=is_active,
            geometry=object.geometry,
            extra=object.extra,
            content_type=content_type,
        )
        set_translated_field(mobile_unit, "name", object.name)
        set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.save()

    logger.info(f"Saved {len(objects)} charging stations to database.")
