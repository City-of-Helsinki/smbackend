# -*- coding: utf-8 -*-

from optparse import make_option
import logging
import json
import datetime

from django.core.management.base import BaseCommand
from django import db
from django.conf import settings
from django.db import transaction
from django.contrib.gis.geos import MultiLineString, LineString, Point, GEOSGeometry

import django.contrib.gis
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping

from services.models import *

class Command(BaseCommand):
    help = "Import ski track units from GeoJSON derived from mSki"
    option_list = list(BaseCommand.option_list + (
        make_option('--helsinki-file', dest='helsinki_filename', help='input filename'),
        make_option('--vantaa-file', dest='vantaa_filename', help='input filename'),
        make_option('--espoo-file', dest='espoo_filename', help='input filename'),
    ))

    def clean_text(self, text):
        #text = text.replace('\n', ' ')
        #text = text.replace(u'\u00a0', ' ')
        # remove consecutive whitespaces
        text = re.sub(r'\s\s+', ' ', text, re.U)
        # remove nil bytes
        text = text.replace('\u0000', ' ')
        text = text.strip()
        return text

    def unit_defaults(self, name, geometry, point):
        return {
            'name_fi': name,
            'provider_type': 101,
            'origin_last_modified_time': datetime.datetime.now(),
            'organization_id': 91,
            'geometry': geometry,
            'location': point
        }

    def import_helsinki_units(self, filename):
        geojson = json.load(open(filename, 'r'))
        for feature in geojson['features']:
            properties = feature['properties']
            geometry = feature['geometry']
            point = Point(geometry['coordinates'][0][0])
            linestrings = [LineString(ls) for ls in geometry['coordinates']]
            multilinestring = MultiLineString(linestrings)
            geom_src = geometry['coordinates']
            if len(geom_src) == 1 and len(geom_src[0]) == 2:
                # There are some tracks with fake route coordinates
                # standing in for a point coord
                multilinestring = None
            defaults = self.unit_defaults(properties['NIMI'], multilinestring, point)
            unit, created = Unit.objects.get_or_create(
                pk=properties['unit_id'],
                defaults=defaults)
            unit.services.add(self.ski_service)

    def import_vantaa_units(self, filename):
        ds = DataSource(filename)
        assert(len(ds) == 1)
        uid = Unit.objects.aggregate(db.models.Max('id'))['id__max']
        while True:
            try:
                Unit.objects.get(pk=uid)
                uid -= 1
            except Unit.DoesNotExist as e:
                break
        lyr = ds[0]
        srs = lyr.srs
        for feat in lyr:
            assert feat.geom_type == 'LineString'
            if type(feat.geom) == django.contrib.gis.gdal.geometries.MultiLineString:
                multilinestring = GEOSGeometry(feat.geom.wkt)
            else:
                multilinestring = MultiLineString(GEOSGeometry(feat.geom.wkt))

            defaults = self.unit_defaults(
                feat.get('nimi'),
                multilinestring,
                Point(feat.geom[0][0], feat.geom[0][1]))
            unit, created = Unit.objects.get_or_create(
                pk=uid,
                defaults=defaults)
            unit.services.add(self.ski_service)
            uid -= 1

    def import_espoo_units(self, filename):
        pass

    def handle(self, **options):
        self.options = options
        self.verbosity = int(options.get('verbosity', 1))
        self.logger = logging.getLogger(__name__)
        self.ski_service = Service.objects.get(pk=33483)
        if self.options.get('helsinki_filename', False):
            self.import_helsinki_units(self.options['helsinki_filename'])
        if self.options.get('vantaa_filename', False):
            self.import_vantaa_units(self.options['vantaa_filename'])
        if self.options.get('espoo_filename', False):
            self.import_espoo_units(self.options['espoo_filename'])
