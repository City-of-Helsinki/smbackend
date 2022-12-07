"""
Note, bicycle stands are not imorter via the wfs importer
as it needs logic to derive if the stand is hull lockable or covered.
"""
import logging
import os

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from munigeo.models import AdministrativeDivision, AdministrativeDivisionGeometry

from mobility_data.models import MobileUnit
from services.models import Unit

from .utils import (
    delete_mobile_units,
    get_closest_address_full_name,
    get_municipality_name,
    get_or_create_content_type,
    get_root_dir,
    get_street_name_translations,
    locates_in_turku,
    set_translated_field,
)

CONTENT_TYPE_NAME = "BicycleStand"
FI_KEY = "fi"
SV_KEY = "sv"
EN_KEY = "en"
NAME_PREFIX = {
    FI_KEY: "Pyöräpysäköinti",
    SV_KEY: "Cykelparkering",
    EN_KEY: "Bicycle parking",
}
BICYCLE_STANDS_SERVICE_ID = settings.BICYCLE_STANDS_IDS["service"]
BICYCLE_STANDS_URL = "{}{}".format(
    settings.TURKU_WFS_URL,
    "?service=WFS&request=GetFeature&typeName=GIS:Polkupyoraparkki&outputFormat=GML3",
)
WFS_SOURCE_DATA_SRID = 3877
GEOJSON_SOURCE_DATA_SRID = 4326
GEOJSON_FILENAME = "bicycle_stands_for_units.geojson"
logger = logging.getLogger("mobility_data")
division_turku = AdministrativeDivision.objects.get(name="Turku")
turku_boundary = AdministrativeDivisionGeometry.objects.get(
    division=division_turku
).boundary


class BicyleStand:

    WFS_HULL_LOCKABLE_STR = "runkolukitusmahdollisuus"
    GEOJSON_HULL_LOCKABLE_STR = "runkolukittava"
    COVERED_IN_STR = "katettu"

    def __init__(self):
        self.geometry = None
        self.model = None
        self.number_of_stands = None
        self.number_of_places = None  # The total number of places for bicycles.
        self.hull_lockable = None
        self.covered = None
        self.city = None
        self.street_address = None
        self.maintained_by_turku = None
        self.name = {}
        self.prefix_name = {}
        self.street_address = {}
        self.related_unit = None

    def set_geojson_feature(self, feature):
        name = feature["kohde"].as_string().strip()
        unit_name = name.split(",")[0]

        self.geometry = GEOSGeometry(feature.geom.wkt, srid=GEOJSON_SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        units_qs = Unit.objects.filter(name=unit_name)
        # Make first unit with same name that is not a Bicycle Stand the related_unit
        for unit in units_qs:
            # Ensure we do not connect to a Bicycle stand unit
            if not unit.services.filter(id=BICYCLE_STANDS_SERVICE_ID):
                self.related_unit = unit
                break

        self.number_of_stands = feature["telineitä"].as_int()
        self.number_of_places = feature["paikkoja"].as_int()
        model_elem = feature["pys.malli"].as_string()
        if model_elem:
            self.model = model_elem

        quality_elem = feature["laatutaso"].as_string()
        if quality_elem:
            quality_text = quality_elem.lower()
            if self.GEOJSON_HULL_LOCKABLE_STR in quality_text:
                self.hull_lockable = True
            else:
                self.hull_lockable = False

            if self.COVERED_IN_STR in quality_text:
                self.covered = True
            else:
                self.covered = False

        self.city = get_municipality_name(self.geometry)
        self.name["fi"] = name
        # If related unit is known, use its translated names
        if self.related_unit:
            self.name["sv"] = self.related_unit.name_sv
            self.name["en"] = self.related_unit.name_en
        else:
            self.name["sv"] = name
            self.name["en"] = name
        self.prefix_name = {k: f"{NAME_PREFIX[k]} {v}" for k, v in self.name.items()}
        addr = feature["osoite"].as_string().split(",")
        # Some addresses are in format:"Pyhän Henrikin aukio, Kupittaankatu 8, 20520 Turku"
        # Then remove the prefix part.
        if len(addr) > 2:
            address = addr[1].strip().split(" ")
        else:
            address = addr[0].strip().split(" ")
        # Street name can have multiple names e.g. Jäkärlän puistokatu 18
        street_name = " ".join(address[:-1])
        if len(address) == 1:
            address_number = ""
        else:
            # The last part is always the number
            address_number = address[-1]
        translated_street_names = get_street_name_translations(street_name, self.city)
        self.street_address["fi"] = f"{translated_street_names['fi']} {address_number}"
        self.street_address["sv"] = f"{translated_street_names['sv']} {address_number}"
        self.street_address["en"] = f"{translated_street_names['en']} {address_number}"

    def set_gml_feature(self, feature):
        object_id = feature["id"].as_string()
        # If ObjectId is set to "0", the bicycle stand is not maintained by Turku
        if object_id == "0":
            self.maintained_by_turku = False
        else:
            self.maintained_by_turku = True

        self.geometry = GEOSGeometry(feature.geom.wkt, srid=WFS_SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)

        model_elem = feature["Malli"]
        if model_elem is not None:
            self.model = model_elem.as_string()
        num_stands_elem = feature["Lukumaara"]
        if num_stands_elem is not None:
            num = num_stands_elem.as_int()
            # for bicycle stands that are Not maintained by Turku
            # the number of stands is set to 0 in the input data
            # but in reality there is no data so None is set.
            if num == 0 and not self.maintained_by_turku:
                self.number_of_stands = None
            else:
                self.number_of_stands = num

        num_places_elem = feature["Pyorapaikkojen_lukumaara"].as_string()

        if num_places_elem:
            # Parse the numbers inside the string and finally sum them.
            # The input can contain string such as "8 runkolukittavaa ja 10 ei runkolukittavaa paikkaa"
            numbers = [int(s) for s in num_places_elem.split() if s.isdigit()]
            self.number_of_places = sum(numbers)

        quality_elem = feature["Pyorapaikkojen_laatutaso"].as_string()

        if quality_elem:
            quality_text = quality_elem.lower()
            if self.WFS_HULL_LOCKABLE_STR in quality_text:
                self.hull_lockable = True
            else:
                self.hull_lockable = False

            if self.COVERED_IN_STR in quality_text:
                self.covered = True
            else:
                self.covered = False
        self.city = get_municipality_name(self.geometry)
        full_names = get_closest_address_full_name(self.geometry)
        self.name[FI_KEY] = full_names[FI_KEY]
        self.name[SV_KEY] = full_names[SV_KEY]
        self.name[EN_KEY] = full_names[EN_KEY]
        self.prefix_name = {k: f"{NAME_PREFIX[k]} {v}" for k, v in self.name.items()}


def get_bicycle_stand_objects(data_source=None):
    """
    Returns a list containg instances of BicycleStand class.
    """
    data_sources = []

    if data_source:
        data_sources.append(data_source)
    else:
        # Add the WFS datasource that is in GML format
        ds = DataSource(BICYCLE_STANDS_URL)
        data_sources.append(("gml", ds))
        # Add the GEOJSON datasource which is a file
        data_path = os.path.join(get_root_dir(), "mobility_data/data")
        file_path = os.path.join(data_path, GEOJSON_FILENAME)
        ds = DataSource(file_path)
        data_sources.append(("geojson", ds))

    bicycle_stands = []
    """
    external_stands dict is used to keep track of the names of imported external stands
    (i.e. not maintained by Turku.)The name is the key and the value is Bool.
    i.e. Only one bicycle stand which point data points to same address is added.
    """
    external_stands = {}
    for data_source in data_sources:
        for feature in data_source[1][0]:
            source_data_srid = (
                WFS_SOURCE_DATA_SRID
                if data_source[0] == "gml"
                else GEOJSON_SOURCE_DATA_SRID
            )
            if locates_in_turku(feature, source_data_srid):
                bicycle_stand = BicyleStand()
                if data_source[0] == "gml":
                    bicycle_stand.set_gml_feature(feature)
                elif data_source[0] == "geojson":
                    bicycle_stand.set_geojson_feature(feature)
                if (
                    bicycle_stand.name[FI_KEY] not in external_stands
                    and not bicycle_stand.maintained_by_turku
                ):
                    external_stands[bicycle_stand.name[FI_KEY]] = True
                    bicycle_stands.append(bicycle_stand)
                elif bicycle_stand.maintained_by_turku:
                    bicycle_stands.append(bicycle_stand)

    logger.info(f"Retrieved {len(bicycle_stands)} bicycle stands.")
    return bicycle_stands


@db.transaction.atomic
def delete_bicycle_stands():
    delete_mobile_units(CONTENT_TYPE_NAME)


@db.transaction.atomic
def create_bicycle_stand_content_type():
    description = "Bicycle stands in The Turku Region."
    content_type, _ = get_or_create_content_type(CONTENT_TYPE_NAME, description)
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_bicycle_stands()

    content_type = create_bicycle_stand_content_type()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type,
        )
        extra = {}
        extra["model"] = object.model
        extra["maintained_by_turku"] = object.maintained_by_turku
        extra["number_of_stands"] = object.number_of_stands
        extra["number_of_places"] = object.number_of_places
        extra["hull_lockable"] = object.hull_lockable
        extra["covered"] = object.covered
        mobile_unit.extra = extra
        mobile_unit.geometry = object.geometry
        set_translated_field(mobile_unit, "name", object.name)
        if object.street_address:
            set_translated_field(mobile_unit, "address", object.street_address)
        mobile_unit.save()
