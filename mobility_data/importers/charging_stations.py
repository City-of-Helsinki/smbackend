import csv
import logging

from django.conf import settings
from django.contrib.gis.geos import Point
from munigeo.models import Municipality

from .utils import (
    get_full_csv_file_name,
    get_municipality_name,
    get_postal_code,
    get_street_name_translations,
    LANGUAGES,
    MobileUnitDataBase,
)

logger = logging.getLogger("mobility_data")

CHARGING_STATION_SERVICE_NAMES = {
    "fi": "Autojen sähkölatauspiste",
    "sv": "Elladdningsstation för bilar",
    "en": "Car e-charging point",
}
SOURCE_DATA_FILE_NAME = "LatauspisteetTurku.csv"
SOURCE_DATA_SRID = 3877
CONTENT_TYPE_NAME = "ChargingStation"
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


class ChargingStation(MobileUnitDataBase):
    def __init__(self, values):
        super().__init__()
        self.extra["chargers"] = []
        self.extra["administrator"] = {}
        # Contains Only steet_name and number
        x = float(values["x"].replace(",", "."))
        y = float(values["y"].replace(",", "."))
        self.geometry = Point(x, y, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra["charge_target"] = values["charge_target"]
        self.extra["method_of_use"] = values["method_of_use"]
        self.extra["other"] = values["other"]
        self.extra["payment"] = values["payment"]
        try:
            self.municipality = Municipality.objects.get(
                name=get_municipality_name(self.geometry)
            )
        except Municipality.DoesNotExist:
            self.municipality = None
        self.address_zip = get_postal_code(self.geometry)
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


def get_charging_station_objects():
    # Store the imported stations to dict, the index is the key.
    file_name = get_full_csv_file_name(SOURCE_DATA_FILE_NAME, CONTENT_TYPE_NAME)
    charging_stations = {}
    column_mappings = {}
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
            if line_count >= number_of_rows:
                break
    # create list from dict values.
    objects = [obj for obj in charging_stations.values()]
    return objects
