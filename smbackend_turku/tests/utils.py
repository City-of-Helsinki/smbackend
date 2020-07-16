import os
import json

from django.conf import settings
from munigeo.models import Municipality
from django.contrib.gis.geos import Point


def create_municipality():
    Municipality.objects.create(id="turku", name="Turku", name_fi="Turku", name_sv="Åbo")


def get_location(latitude, longitude, srid):
    point = Point(x=float(latitude), y=float(longitude), srid=srid)
    point.transform(settings.DEFAULT_SRID)
    return point
