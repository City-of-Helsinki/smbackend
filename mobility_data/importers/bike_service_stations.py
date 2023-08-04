import logging

from django.conf import settings
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    get_file_name_from_data_source,
    get_root_dir,
    get_street_name_translations,
    MobileUnitDataBase,
)

logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 3877
GEOJSON_FILENAME = "Pyorienkorjauspisteet_2022.geojson"
LANGUAGES = [language[0] for language in settings.LANGUAGES]
CONTENT_TYPE_NAME = "BikeServiceStation"


class BikeServiceStation(MobileUnitDataBase):
    def __init__(self, feature):
        super().__init__()
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        targets = feature["Kohde"].as_string().split("/")
        targets = [target.strip() for target in targets]
        description = feature["Kuvaus"].as_string().split("\n")

        # Addresses are in format:
        # Uudenmaankatu 18, 20700 Turku / Nylandsgatan 18, 20700 Turku
        addresses = feature["Osoite"].as_string().split("/")
        self.address_zip, municipality = addresses[0].split(",")[1].strip().split(" ")
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
                    ] = f"{get_street_name_translations(street_name, municipality)[language]} number"
                # Source data does not contain English addresses, assign the Finnsh
                else:
                    self.address[language] = addresses[0]
        try:
            self.municipality = Municipality.objects.get(name=municipality)
        except Municipality.DoesNotExist:
            self.municipality = None
        self.extra["additional_details"] = feature["Lisätieto"].as_string()
        self.extra["in_terrain"] = feature["Maastossa"].as_string()


def get_data_layer():
    file_name = get_file_name_from_data_source(CONTENT_TYPE_NAME)
    if not file_name:
        file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    else:
        file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    data_layer = GDALDataSource(file_name)[0]
    return data_layer


def get_bike_service_station_objects():
    bicycle_repair_points = []
    for feature in get_data_layer():
        bicycle_repair_points.append(BikeServiceStation(feature))
    return bicycle_repair_points
