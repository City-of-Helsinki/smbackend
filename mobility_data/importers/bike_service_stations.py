import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_or_create_content_type,
    get_street_name_translations,
    set_translated_field,
)
from mobility_data.models import ContentType, DataSource, MobileUnit

logger = logging.getLogger("bicycle_network")
SOURCE_DATA_SRID = 3877
GEOJSON_FILENAME = "Pyorienkorjauspisteet_2022.geojson"
LANGUAGES = [language[0] for language in settings.LANGUAGES]


class BikeServiceStation:
    def __init__(self, feature):
        self.name = {}
        self.address = {}
        self.description = {}
        self.extra = {}
        self.address = {}
        self.zip_code = None
        self.municipality = None
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        targets = feature["Kohde"].as_string().split("/")
        targets = [target.strip() for target in targets]
        description = feature["Kuvaus"].as_string().split("\n")

        # Addresses are in format:
        # Uudenmaankatu 18, 20700 Turku / Nylandsgatan 18, 20700 Turku
        addresses = feature["Osoite"].as_string().split("/")
        self.zip_code, self.municipality = addresses[0].split(",")[1].strip().split(" ")
        # remove zip code and municipality
        addresses = [address.split(",")[0].strip() for address in addresses]
        for i, language in enumerate(LANGUAGES):
            if i < len(targets):
                self.name[language] = targets[i]
            else:
                # if no target found for the language, assign the Finnish to it
                self.name[language] = targets[0]

            self.description[language] = description[i]

            if i < len(addresses):
                self.address[language] = addresses[i]
            else:
                # If no swedish address, retrieve it from the database.
                if language == "sv":
                    street_name, number = addresses[0].split(" ")
                    self.address[
                        language
                    ] = f"{get_street_name_translations(street_name, self.municipality)[language]} number"
                # Source data does not contain English addresses, assign the Finnsh
                else:
                    self.address[language] = addresses[0]

        self.extra["additional_details"] = feature["Lisätieto"].as_string()
        self.extra["in_terrain"] = feature["Maastossa"].as_string()


def get_bike_service_station_objects(geojson_file=None):
    bicycle_repair_points = []
    file_name = None
    if hasattr(settings, "PROJECT_ROOT"):
        root_dir = settings.PROJECT_ROOT
    else:
        root_dir = settings.BASE_DIR

    if not geojson_file:
        data_source_qs = DataSource.objects.filter(
            type_name=ContentType.BIKE_SERVICE_STATION
        )
        # If data source found, use the uploaded data file.
        if data_source_qs.exists():
            file_name = str(data_source_qs.first().data_file.file)
        else:
            file_name = f"{root_dir}/mobility_data/data/{GEOJSON_FILENAME}"
    else:
        # Use the test data file
        file_name = f"{root_dir}/mobility_data/tests/data/{geojson_file}"

    data_layer = GDALDataSource(file_name)[0]
    for feature in data_layer:
        bicycle_repair_points.append(BikeServiceStation(feature))
    return bicycle_repair_points


@db.transaction.atomic
def delete_bike_service_stations():
    delete_mobile_units(ContentType.BICYCLE_STAND)


@db.transaction.atomic
def create_bike_service_station_content_type():
    description = "Bike service stations The Turku Region."
    name = "Bike service station"
    content_type, _ = get_or_create_content_type(
        ContentType.BIKE_SERVICE_STATION, name, description
    )
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_bike_service_stations()

    content_type = create_bike_service_station_content_type()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type, extra=object.extra
        )
        set_translated_field(mobile_unit, "name", object.name)
        set_translated_field(mobile_unit, "description", object.description)
        set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.save()
