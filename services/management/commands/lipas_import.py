# -*- coding: utf-8 -*-

import ijson.backends.yajl2 as ijson
import requests
import requests_cache
from urllib.request import urlopen
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon, MultiPolygon, LineString

from services.models import UnitIdentifier


#requests_cache.install_cache('lipas')

URL_BASE = 'http://lipas.cc.jyu.fi/geoserver/lipas/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=%s&outputFormat=application/json'

def download(unit_map, layer_name):
    url = URL_BASE % layer_name
    #fp = urlopen(url)
    fp = open('lipas_alueet.dat', 'rb')
    features = ijson.items(fp, 'features.item')
    i = 0
    for idx, feat in enumerate(features):
        geom = feat['geometry']
        feat_id = str(feat['properties']['id'])
        unit_id = unit_map.get(str(feat['properties']['id']), None)
        if geom['type'] == 'LineString':
            geom_obj = LineString(geom['coordinates'], srid=3067)
        elif geom['type'] == 'Polygon':
            coords = geom['coordinates']
            geom_obj = Polygon(*coords, srid=3067)
        if idx % 100 == 0:
            print(idx)
        from pprint import pprint
        pprint(feat)

class Command(BaseCommand):
    help = "Import sports venues from Lipas"

    def handle(self, **options):
        ids = UnitIdentifier.objects.filter(namespace='lipas').values_list('unit_id', 'value')
        units_by_lipas_id = {x[1]: x[0] for x in ids}
        download(units_by_lipas_id, 'lipas:lipas_kaikki_alueet')
