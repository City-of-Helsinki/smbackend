import logging
from enum import Enum

from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_file_name_from_data_source,
    get_or_create_content_type,
    get_root_dir,
)
from mobility_data.models import ContentType, MobileUnit

logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 3877

GEOJSON_FILENAME = "autopysäköinti_eihlö.geojson"
LANGUAGES = [language[0] for language in settings.LANGUAGES]


class FieldTypes(Enum):
    STRING = 1
    MULTILANG_STRING = 2
    INTEGER = 3
    FLOAT = 4


class NoStaffParking:
    extra_field_mappings = {
        "saavutettavuus": {
            "name": "accessability",
            "type": FieldTypes.MULTILANG_STRING,
        },
        "paikkoja_y": {"name": "places", "type": FieldTypes.INTEGER},
        "invapaikkoja": {"name": "places_for_disabled", "type": FieldTypes.INTEGER},
        "sahkolatauspaikkoja": {
            "name": "e_charging_points",
            "type": FieldTypes.INTEGER,
        },
        "tolppapaikkoja": {"name": "post_positions", "type": FieldTypes.INTEGER},
        "rajoitukset/maksullisuus": {"name": "limits_fees", "type": FieldTypes.STRING},
        "aikarajoitus": {"name": "time_limit", "type": FieldTypes.STRING},
        "paivays": {"name": "timestamp", "type": FieldTypes.STRING},
        "lastauspiste": {"name": "lastauspiste", "type": FieldTypes.MULTILANG_STRING},
        "lisatietoja": {
            "name": "additinal_information",
            "type": FieldTypes.MULTILANG_STRING,
        },
        "rajoitustyyppi": {"name": "limit_type", "type": FieldTypes.MULTILANG_STRING},
        "maksuvyohyke": {"name": "payment_zone", "type": FieldTypes.INTEGER},
        "max_aika_h": {"name": "max_time_h", "type": FieldTypes.FLOAT},
        "max_aika_m": {"name": "max_time_m", "type": FieldTypes.FLOAT},
        "rajoitus_maksul_arki": {
            "name": "limit_payment_weekday",
            "type": FieldTypes.STRING,
        },
        "rajoitus_maksul_l": {
            "name": "limit_payment_saturday",
            "type": FieldTypes.STRING,
        },
        "rajoitus_maksul_s": {
            "name": "limit_payment_sunday",
            "type": FieldTypes.STRING,
        },
        "rajoitettu_ark": {"name": "limited_weekday", "type": FieldTypes.STRING},
        "rajoitettu_l": {"name": "limited_saturday", "type": FieldTypes.STRING},
        "rajoitettu_s": {"name": "limited_sunday", "type": FieldTypes.STRING},
        "voimassaolokausi": {"name": "validity_period", "type": FieldTypes.STRING},
        "rajoit_lisat": {
            "name": "limit_extra_info",
            "type": FieldTypes.MULTILANG_STRING,
        },
        "varattu_tiet_ajon": {"name": "reserved_for", "type": FieldTypes.STRING},
        "erityisluv": {"name": "extra_permission", "type": FieldTypes.STRING},
        "vuoropys": {"name": "shift_parking", "type": FieldTypes.STRING},
        "talvikunno": {"name": "winter_maintenance", "type": FieldTypes.STRING},
    }

    def __init__(self, feature):
        # TODO, add multilang Address, when data available
        # self.address = {}
        # TODO, Add multilang name when data available
        # self.name = {}
        self.address = feature["osoite"].as_string().split(",")[0]
        self.name = feature["kohde"].as_string()
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra = {}
        for field in feature.fields:
            if field in self.extra_field_mappings:
                field_name = self.extra_field_mappings[field]["name"]
                match self.extra_field_mappings[field]["type"]:
                    case FieldTypes.STRING:
                        self.extra[field_name] = feature[field].as_string()
                    case FieldTypes.MULTILANG_STRING:
                        self.extra[field_name] = {}
                        field_content = feature[field].as_string()
                        if field_content:
                            strings = feature[field].as_string().split("/")
                            for i, lang in enumerate(LANGUAGES):
                                if i < len(strings):
                                    self.extra[field_name][lang] = strings[i].strip()
                    case FieldTypes.INTEGER:
                        self.extra[field_name] = feature[field].as_int()
                    case FieldTypes.FLOAT:
                        self.extra[field_name] = feature[field].as_double()


def get_no_staff_parking_objects(geojson_file=None):
    no_staff_parkings = []
    file_name = None

    if not geojson_file:
        file_name = get_file_name_from_data_source(ContentType.NO_STAFF_PARKING)
        if not file_name:
            file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    data_layer = GDALDataSource(file_name)[0]
    for feature in data_layer:
        no_staff_parkings.append(NoStaffParking(feature))
    return no_staff_parkings


@db.transaction.atomic
def delete_no_staff_parkings():
    delete_mobile_units(ContentType.NO_STAFF_PARKING)


@db.transaction.atomic
def create_no_staff_parking_content_type():
    description = "No staff parkings in the Turku region."
    name = "No staff parking"
    content_type, _ = get_or_create_content_type(
        ContentType.NO_STAFF_PARKING, name, description
    )
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_no_staff_parkings()

    content_type = create_no_staff_parking_content_type()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type, extra=object.extra, geometry=object.geometry
        )
        mobile_unit.address = object.address
        mobile_unit.name = object.name
        # set_translated_field(mobile_unit, "name", object.name)
        # set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.save()
