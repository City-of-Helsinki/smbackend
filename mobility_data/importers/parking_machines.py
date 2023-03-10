from django import db
from django.conf import settings
from django.contrib.gis.geos import Point

from mobility_data.models import MobileUnit

from .utils import (
    delete_mobile_units,
    FieldTypes,
    get_file_name_from_data_source,
    get_or_create_content_type_from_config,
    get_root_dir,
    set_translated_field,
)

SOURCE_DATA_SRID = 4326
GEOJSON_FILENAME = "parking_machines.geojson"
CONTENT_TYPE_NAME = "ParkingMachine"
LANGUAGES = ["fi", "sv", "en"]


class ParkingMachine:

    extra_field_mappings = {
        "Sijainti": {
            "type": FieldTypes.MULTILANG_STRING,
            "fi": "Sijainti",
            "sv": "Plats",
            "en": "Location",
        },
        "Virta": {
            "type": FieldTypes.MULTILANG_STRING,
            "fi": "Virta",
            "sv": "Ström",
            "en": "Power",
        },
        "Maksutapa": {
            "type": FieldTypes.MULTILANG_STRING,
            "fi": "Maksutapa",
            "sv": "Betalningssätt",
            # The source data contains Payment method with method starting with
            # uppercase M and lowercase m.
            "en": ["Payment method", "Payment Method"],
        },
        "Näyttö": {
            "type": FieldTypes.MULTILANG_STRING,
            "fi": "Näyttö",
            "sv": "Skärm",
            "en": "Screen",
        },
        "Omistaja": {
            "type": FieldTypes.MULTILANG_STRING,
            "fi": "Omistaja",
            "sv": "Ägare",
            "en": "Owner",
        },
        "Maksuvyöhyke": {
            "type": FieldTypes.MULTILANG_STRING,
            "fi": "Maksuvyöhyke",
            "sv": "Zon",
            "en": "Zone",
        },
        "Muuta": {"type": FieldTypes.STRING},
        "Taksa/h": {"type": FieldTypes.FLOAT},
        "Max.aika": {"type": FieldTypes.FLOAT},
        "Malli": {"type": FieldTypes.STRING},
        "Asennettu": {"type": FieldTypes.STRING},
        "Valmistaja": {
            "type": FieldTypes.STRING,
        },
    }

    def __init__(self, feature):
        properties = feature["properties"]
        geometry = feature["geometry"]
        self.extra = {}
        self.address = {"fi": properties["Osoite"]}
        self.address["sv"] = properties["Adress"]
        self.address["en"] = properties["Address"]
        self.geometry = Point(
            geometry["coordinates"][0],
            geometry["coordinates"][1],
            srid=SOURCE_DATA_SRID,
        )
        self.geometry.transform(settings.DEFAULT_SRID)

        for field in properties.keys():
            if field in self.extra_field_mappings:
                match self.extra_field_mappings[field]["type"]:
                    case FieldTypes.MULTILANG_STRING:
                        self.extra[field] = {}
                        for lang in LANGUAGES:
                            key = self.extra_field_mappings[field][lang]
                            # Support multiple keys for same field, e.g.,
                            # 'Payment method' and 'Payment Method'
                            if type(key) == list:
                                for k in key:
                                    val = properties.get(k, None)
                                    if val:
                                        self.extra[field][lang] = val
                                        break
                            else:
                                self.extra[field][lang] = properties[key]

                    case FieldTypes.STRING:
                        self.extra[field] = properties[field]
                    case FieldTypes.INTEGER:
                        val = properties[field]
                        self.extra[field] = int(val) if val else None
                    case FieldTypes.FLOAT:
                        val = properties[field]
                        self.extra[field] = float(val) if val else None


def get_json_data():
    file_name = get_file_name_from_data_source(CONTENT_TYPE_NAME)
    if not file_name:
        file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    json_data = None
    import json

    with open(file_name, "r") as json_file:
        json_data = json.loads(json_file.read())
    return json_data


def get_parking_machine_objects():
    json_data = get_json_data()["features"]
    return [ParkingMachine(feature) for feature in json_data]


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_mobile_units(CONTENT_TYPE_NAME)
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            geometry=object.geometry,
            extra=object.extra,
        )
        mobile_unit.content_types.add(content_type)
        set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.save()
