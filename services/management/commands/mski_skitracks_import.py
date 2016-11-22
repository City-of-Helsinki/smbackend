# -*- coding: utf-8 -*-

from optparse import make_option
import logging
import json
import datetime

from django.core.management.base import BaseCommand
from django import db
from django.conf import settings
from django.db import transaction
from django.contrib.gis.geos import MultiLineString, LineString

from services.models import *

class Command(BaseCommand):
    help = "Import ski track units from GeoJSON derived from mSki"
    option_list = list(BaseCommand.option_list + (
        make_option('-f', '--file', dest='filename', help='input filename'),
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

    def import_units(self, filename):
        geojson = json.load(open(filename, 'r'))
        ski_service = Service.objects.get(pk=33483)
        for feature in geojson['features']:
            properties = feature['properties']
            geometry = feature['geometry']
            defaults = {
                'name_fi': properties['NIMI'],
                'provider_type': 101,
                'origin_last_modified_time': datetime.datetime.now(),
                'organization_id': 91
            }
            unit, created = Unit.objects.get_or_create(
                pk=properties['unit_id'],
                defaults=defaults)
            unit.services.add(ski_service)
            # import pprint
            # pprint.pprint(geometry['coordinates'])
            linestrings = [LineString(ls) for ls in geometry['coordinates']]
            multilinestring = MultiLineString(linestrings)
            unit.geometry = UnitGeometry.objects.create(
                unit_id = properties['unit_id'],
                path = multilinestring
            )

    def handle(self, **options):
        self.options = options
        self.verbosity = int(options.get('verbosity', 1))
        self.logger = logging.getLogger(__name__)
        self.import_units(self.options['filename'])
