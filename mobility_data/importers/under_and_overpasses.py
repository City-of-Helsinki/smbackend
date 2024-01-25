import types

import requests
import xmltodict
from django.conf import settings
from django.contrib.gis.geos import LineString

from mobility_data.importers.constants import TURKU_BBOX

from .utils import MobileUnitDataBase

URL = (
    "https://avoinapi.vaylapilvi.fi/vaylatiedot/digiroad/ows?service=WFS&request=GetFeature"
    f"&typeName=dr_tielinkki_toim_lk&outputFormat=GML3&bbox={TURKU_BBOX},EPSG:4326&srsName=EPSG:4326"
)
UNDERPASS_CONTENT_TYPE_NAME = "Underpass"
OVERPASS_CONTENT_TYPE_NAME = "Overpass"
KUNTAKOODI = "853"
# 8 = kevyenliikenteenväylä
TOIMINN_LK = "8"
PASS_TYPES = types.SimpleNamespace()
PASS_TYPES.OVERPASS = 1
PASS_TYPES.UNDERPASS = -1


def get_json_data(url):
    response = requests.get(URL)
    assert response.status_code == 200
    json_data = xmltodict.parse(response.content)
    return json_data


class Pass(MobileUnitDataBase):
    def __init__(self, feature):
        super().__init__()
        coord_str = feature["digiroad:geom"]["gml:LineString"]["gml:posList"]
        coord_list = coord_str.split(" ")
        coords = ()
        i = 0
        while i < len(coord_list):
            x = coord_list[i]
            y = coord_list[i + 1]
            # discard z, i.e. i+2
            i += 3
            coords += ((float(x), float(y)),)
        self.geometry = LineString(coords, srid=4326)
        self.geometry.transform(settings.DEFAULT_SRID)


def get_under_and_overpass_objects():
    json_data = get_json_data(URL)
    overpasses = []
    underpasses = []
    for feature in json_data["wfs:FeatureCollection"]["gml:featureMembers"][
        "digiroad:dr_tielinkki_toim_lk"
    ]:

        if (
            feature.get("digiroad:kuntakoodi", None) == KUNTAKOODI
            and feature.get("digiroad:toiminn_lk", None) == TOIMINN_LK
        ):
            silta_alik = int(feature.get("digiroad:silta_alik", None))
            match silta_alik:
                case PASS_TYPES.UNDERPASS:
                    underpasses.append(Pass(feature))
                case PASS_TYPES.OVERPASS:
                    overpasses.append(Pass(feature))
    return underpasses, overpasses
