import logging

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    delete_mobile_units,
    FieldTypes,
    get_file_name_from_data_source,
    get_or_create_content_type,
    get_root_dir,
    set_translated_field,
)
from mobility_data.models import ContentType, MobileUnit

logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 3877
GEOJSON_FILENAME = "loading_and_unloading_places.geojson"
LANGUAGES = [language[0] for language in settings.LANGUAGES]


class LoadingPlace:

    extra_field_mappings = {
        "Saavutetta": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "Lastaus": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "Lisatieto": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "Muutanimi": {
            "type": FieldTypes.MULTILANG_STRING,
        },
    }

    def __init__(self, feature):
        self.address = {}
        self.name = {}
        addresses = [
            " ".join(a.strip().split(" ")[:-2]).rstrip(",")
            for a in feature["osoite"].as_string().split("/")
        ]

        self.address_zip, municipality = (
            feature["osoite"].as_string().split("/")[0].strip().split(" ")[-2:]
        )
        names = [n.strip() for n in feature["Kohteet"].as_string().split("/")]
        for i, lang in enumerate(LANGUAGES):
            if i < len(addresses):
                self.address[lang] = addresses[i]
            else:
                # assign Fi if translation not found
                self.address[lang] = addresses[0]
            if i < len(names):
                self.name[lang] = names[i]
            else:
                self.name[lang] = names[0]

        try:
            municipality = Municipality.objects.get(name=municipality)
            self.municipality = municipality
        except Municipality.DoesNotExist:
            self.municipality = None
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra = {}
        for field in feature.fields:
            if field in self.extra_field_mappings:
                # It is possible to define a name in the extra_field_mappings
                # and this name will be used in the extra field and serialized data.
                if hasattr(self.extra_field_mappings[field], "name"):
                    field_name = self.extra_field_mappings[field]["name"]
                else:
                    field_name = field
                match self.extra_field_mappings[field]["type"]:
                    # Source data contains currently only MULTILANG_STRINGs
                    case FieldTypes.MULTILANG_STRING:
                        self.extra[field_name] = {}
                        field_content = feature[field].as_string()
                        if field_content:
                            strings = field_content.split("/")
                            for i, lang in enumerate(LANGUAGES):
                                if i < len(strings):
                                    self.extra[field_name][lang] = strings[i].strip()


def get_loading_and_unloading_objects(geojson_file=None):
    objects = []
    file_name = None

    if not geojson_file:
        file_name = get_file_name_from_data_source(ContentType.LOADING_UNLOADING_PLACE)
        if not file_name:
            file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    else:
        # Use the test data file
        file_name = f"{get_root_dir()}/mobility_data/tests/data/{geojson_file}"

    data_layer = GDALDataSource(file_name)[0]
    for feature in data_layer:
        objects.append(LoadingPlace(feature))
    return objects


@db.transaction.atomic
def delete_loading_and_unloading_places():
    delete_mobile_units(ContentType.LOADING_UNLOADING_PLACE)


@db.transaction.atomic
def get_and_create_loading_and_unloading_place_content_type():
    description = "Loading and uloading places in the Turku region."
    name = "Loading and unloading place."
    content_type, _ = get_or_create_content_type(
        ContentType.LOADING_UNLOADING_PLACE, name, description
    )
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_loading_and_unloading_places()

    content_type = get_and_create_loading_and_unloading_place_content_type()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type,
            extra=object.extra,
            geometry=object.geometry,
        )
        set_translated_field(mobile_unit, "name", object.name)
        set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.address_zip = object.address_zip
        mobile_unit.municipality = object.municipality
        mobile_unit.save()
