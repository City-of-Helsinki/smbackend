import os
import json

from django.conf import settings
from munigeo.models import Municipality
from django.contrib.gis.geos import Point

from smbackend_turku.importers.utils import get_weekday_str


def create_municipality():
    Municipality.objects.create(id="turku", name="Turku", name_fi="Turku", name_sv="Åbo")


def get_test_resource():
    test_dir = os.path.dirname(__file__)
    file = os.path.join(test_dir, "data/units.json")

    with open(file) as file:
        data = json.load(file)
    return data


def format_time(time_str):
    if not time_str:
        return ''
    parts = time_str.split(':')[:2]
    parts[0] = str(int(parts[0]))
    return ':'.join(parts)


def get_opening_hours(opening_time, closing_time, weekday):
    opening_time = format_time(opening_time)
    closing_time = format_time(closing_time)
    weekday_str = '–'.join([get_weekday_str(int(wd), 'fi') if wd else '' for wd in weekday.split('-')])
    return '{}&nbsp;{}–{}'.format(weekday_str, opening_time, closing_time)


def get_location(latitude, longitude, srid):
    point = Point(x=float(latitude), y=float(longitude), srid=srid)
    point.transform(settings.DEFAULT_SRID)
    return point
