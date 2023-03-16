import logging

from django.conf import settings
from django.contrib.gis.geos import Point, Polygon
from munigeo.models import Municipality

from .constants import SOUTHWEST_FINLAND_BOUNDARY, SOUTHWEST_FINLAND_BOUNDARY_SRID
from .utils import (
    fetch_json,
    get_street_name_and_number,
    get_street_name_translations,
    LANGUAGES,
    MobileUnitDataBase,
)

logger = logging.getLogger("mobility_data")
GAS_FILLING_STATIONS_URL = (
    "https://services1.arcgis.com/rhs5fjYxdOG1Et61/ArcGIS/rest/services/GasFillingStations/FeatureServer/0/query"
    "?f=json&where=1%3D1&outFields=OPERATOR%2CLAT%2CLON%2CSTATION_NAME%2CADDRESS%2CCITY%2CZIP_CODE%2CLNG_CNG%2CObjectId"
)

CONTENT_TYPE_NAME = "GasFillingStation"


class GasFillingStation(MobileUnitDataBase):
    def __init__(self, elem, srid=settings.DEFAULT_SRID):
        super().__init__()
        attributes = elem.get("attributes")
        x = attributes.get("LON", 0)
        y = attributes.get("LAT", 0)
        self.geometry = Point(x, y, srid=srid)
        self.name["fi"] = attributes.get("STATION_NAME", "")
        address_field = attributes.get("ADDRESS", "")
        street_name, street_number = get_street_name_and_number(address_field)
        self.address_zip = attributes.get("ZIP_CODE", "")
        municipality_name = attributes.get("CITY", "")
        translated_street_names = get_street_name_translations(
            street_name, municipality_name
        )
        try:
            self.municipality = Municipality.objects.get(name=municipality_name)
        except Municipality.DoesNotExist:
            self.municipality = None

        for lang in LANGUAGES:
            if street_number:
                self.address[lang] = f"{translated_street_names[lang]} {street_number}"
            else:
                self.address[lang] = f"{translated_street_names[lang]}"

        self.operator = attributes.get("OPERATOR", "")
        self.lng_cng = attributes.get("LNG_CNG", "")
        self.extra["operator"] = self.operator
        self.extra["lng_cng"] = self.lng_cng


def get_filtered_gas_filling_station_objects(json_data=None):
    """
    Returns a list of GasFillingStation objects that are filtered by location.
    Stations inside boundarys of Southwest Finland are included, the rest
    are discarded.
    """

    if not json_data:
        json_data = fetch_json(GAS_FILLING_STATIONS_URL)
    # srid = json_data["spatialReference"]["wkid"]
    # NOTE, hack to fix srid 102100 in source data causes "crs not found"
    srid = 4326
    # Create list of all GasFillingStation objects
    objects = [GasFillingStation(data, srid=srid) for data in json_data["features"]]
    # Filter objects by their location
    # Polygon used the detect if point intersects. i.e. is in the boundaries of SouthWest Finland.
    polygon = Polygon(SOUTHWEST_FINLAND_BOUNDARY, srid=SOUTHWEST_FINLAND_BOUNDARY_SRID)
    filtered_objects = [o for o in objects if polygon.covers(o.geometry)]
    logger.info(
        "Filtered: {} gas filling stations by location to: {}.".format(
            len(json_data["features"]), len(filtered_objects)
        )
    )
    return filtered_objects
