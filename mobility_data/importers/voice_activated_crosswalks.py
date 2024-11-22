import json

from django.conf import settings
from django.contrib.gis.geos import LineString

from .utils import get_file_name_from_data_source, get_root_dir, MobileUnitDataBase

SOURCE_DATA_SRID = 3067
GEOJSON_FILENAME = "voice_activated_crosswalks.geojson"
CONTENT_TYPE_NAME = "VoiceActivatedCrosswalk"


class VoiceActivatedCrosswalk(MobileUnitDataBase):

    def __init__(self, feature):
        super().__init__()
        coords = feature["geometry"]["coordinates"]
        self.geometry = LineString(coords, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)


def get_json_data():
    file_name = get_file_name_from_data_source(CONTENT_TYPE_NAME)
    if not file_name:
        file_name = f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"
    json_data = None

    with open(file_name, "r") as json_file:
        json_data = json.loads(json_file.read())
    return json_data


def get_parking_machine_objects():
    json_data = get_json_data()["features"]
    return [VoiceActivatedCrosswalk(feature) for feature in json_data]
