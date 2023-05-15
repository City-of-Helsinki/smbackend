import xml.etree.ElementTree as ET

import requests
import xmltodict
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, LineString, MultiPolygon, Polygon
from django.core.management import BaseCommand

from mobility_data.importers.under_and_overpasses import get_over_and_underpass_objects


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.get(URL)
        content_string = response.content.decode("utf-8")
        # xml_string = ET.ElementTree(ET.fromstring(content_string))
        json_data = xmltodict.parse(response.content)
        num_ali = 0
        num_yli = 0
        num_oth = 0
        for feature in json_data["wfs:FeatureCollection"]["gml:featureMembers"][
            "digiroad:dr_tielinkki_toim_lk"
        ]:
            if (
                feature.get("digiroad:KUNTAKOODI", None) == "853"
                and feature.get("digiroad:TOIMINN_LK", None) == "8"
            ):
                silta_alik = int(feature.get("digiroad:SILTA_ALIK", None))
                created = False
                if silta_alik == -1:
                    num_ali += 1
                    createad = True
                elif silta_alik == 1:
                    num_yli += 1
                    created = True
                else:
                    num_oth += 1
                if created:
                    coord_str = feature["digiroad:SHAPE"]["gml:LineString"][
                        "gml:posList"
                    ]
                    # Split the string into a list of coordinate pairs
                    coords = ()
                    for x, y in pairwise(coord_str.split(" ")):
                        coords += ((float(x), float(y)),)
                    LineString(coords, srid=426)
                    breakpoint()
        print(
            "yli: " + str(num_yli) + " ali " + str(num_ali) + " num_oth " + str(num_oth)
        )
        breakpoint()
        # breakpoint()
        # ds = DataSource(URL)
        # breakpoint()
        # layer = ds[0]
        # for feature in layer:
        #     breakpoint()
