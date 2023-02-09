from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry

from mobility_data.models import MobileUnit

from .utils import (
    delete_mobile_units,
    FieldTypes,
    get_file_name_from_data_source,
    get_or_create_content_type,
    get_root_dir,
)

SOURCE_DATA_SRID = 4326
GEOJSON_FILENAME = "parking_machines.geojson"
CONTENT_TYPE_NAME = "ParkingMachine"


class ParkingMachine:
    extra_field_mappings = {
        "Sijainti": {"type": FieldTypes.STRING},
        "Valmistaja": {"type": FieldTypes.STRING},
        "Malli": {"type": FieldTypes.STRING},
        "Asennettu": {"type": FieldTypes.STRING},
        "Virta": {"type": FieldTypes.STRING},
        "Maksutapa": {"type": FieldTypes.STRING},
        "Näyttö": {"type": FieldTypes.STRING},
        "Muuta": {"type": FieldTypes.STRING},
        "Omistaja": {"type": FieldTypes.STRING},
        "Taksa/h": {"type": FieldTypes.FLOAT},
        "Max.aika": {"type": FieldTypes.FLOAT},
        "Maksuvyöhyke": {"type": FieldTypes.STRING},
    }

    def __init__(self, feature):
        self.extra = {}
        self.address = feature["Osoite"].as_string()
        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        for field in feature.fields:
            if field in self.extra_field_mappings:
                match self.extra_field_mappings[field]["type"]:
                    case FieldTypes.STRING:
                        self.extra[field] = feature[field].as_string()
                    case FieldTypes.INTEGER:
                        self.extra[field] = feature[field].as_int()
                    case FieldTypes.FLOAT:
                        self.extra[field] = feature[field].as_double()


def get_data_layer():
    file_name = get_file_name_from_data_source(CONTENT_TYPE_NAME)
    if not file_name:
        file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    ds = GDALDataSource(file_name)
    assert len(ds) == 1
    return ds[0]


def get_parking_machine_objects():
    data_layer = get_data_layer()
    return [ParkingMachine(feature) for feature in data_layer]


@db.transaction.atomic
def get_and_create_parking_machine_content_type():
    description = "Parking machines in the city of Turku."
    content_type, _ = get_or_create_content_type(CONTENT_TYPE_NAME, description)
    return content_type


@db.transaction.atomic
def save_to_database(objects, delete_tables=True):
    if delete_tables:
        delete_mobile_units(CONTENT_TYPE_NAME)

    content_type = get_and_create_parking_machine_content_type()
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            address=object.address,
            geometry=object.geometry,
            extra=object.extra,
        )
        mobile_unit.content_types.add(content_type)
