import datetime
import logging

import pytz
from django import db
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import Point, Polygon
from munigeo.importer.sync import ModelSyncher
from munigeo.utils import get_default_srid

from services.models import Unit, UnitEntrance

from .utils import clean_text, pk_get, save_translated_field

UTC_TIMEZONE = pytz.timezone("UTC")
PROJECTION_SRID = get_default_srid()
VERBOSITY = True
LOGGER = logging.getLogger(__name__)
CACHED_UNIT = None


def import_entrances(fetch_resource=pk_get):
    obj_list = fetch_resource("entrance")
    syncher = ModelSyncher(UnitEntrance.objects.all(), lambda obj: obj.id)

    target_srid = PROJECTION_SRID
    bounding_box = Polygon.from_bbox(settings.BOUNDING_BOX)
    bounding_box.srid = 4326
    gps_srs = SpatialReference(4326)
    target_srs = SpatialReference(target_srid)
    target_to_gps_ct = CoordTransform(target_srs, gps_srs)
    bounding_box.transform(target_to_gps_ct)
    gps_to_target_ct = CoordTransform(gps_srs, target_srs)

    for info in sorted(obj_list, key=lambda x: x["unit_id"]):
        _import_unit_entrance(
            syncher,
            info.copy(),
            bounding_box,
            gps_to_target_ct,
            target_srid,
        )

    syncher.finish()
    return syncher


@db.transaction.atomic
def _import_unit_entrance(
    syncher,
    info,
    bounding_box,
    gps_to_target_ct,
    target_srid,
):
    obj = syncher.get(info["id"])
    obj_changed = False
    obj_created = False
    if not obj:
        obj = UnitEntrance(id=info["id"])
        global CACHED_UNIT
        if CACHED_UNIT and CACHED_UNIT.id == info["unit_id"]:
            obj.unit = CACHED_UNIT
        else:
            try:
                obj.unit = Unit.objects.get(pk=info["unit_id"])
            except Unit.DoesNotExist:
                if VERBOSITY:
                    LOGGER.warning("Unit with id (%d) not found" % info["unit_id"])
                return
        CACHED_UNIT = obj.unit
        obj_changed = True
        obj_created = True

    if save_translated_field(obj, "name", info, "name"):
        obj_changed = True

    fields = [
        "picture_url",
        "streetview_url",
    ]

    for field in fields:
        if field not in info or clean_text(info[field]) == "":
            if getattr(obj, field) is not None:
                setattr(obj, field, None)
                obj_changed = True
        elif info[field] != getattr(obj, field):
            setattr(obj, field, clean_text(info.get(field)))
            obj_changed = True

    is_main_entrance = info["is_main_entrance"] == "Y"
    if is_main_entrance != obj.is_main_entrance:
        obj.is_main_entrance = is_main_entrance
        obj_changed = True

    n = float(info.get("latitude", 0))
    e = float(info.get("longitude", 0))
    location = None
    if n and e:
        p = Point(e, n, srid=4326)
        if p.within(bounding_box):
            if target_srid != 4326:
                p.transform(gps_to_target_ct)
            location = p
        else:
            if VERBOSITY:
                LOGGER.warning("Invalid coordinates (%f, %f) for %s" % (n, e, obj))

    if location and obj.location:
        # If the distance is less than 10cm, assume the location
        # hasn't changed.
        assert obj.location.srid == PROJECTION_SRID
        if location.distance(obj.location) < 0.10:
            location = obj.location

    if location != obj.location:
        obj_changed = True
        obj.location = location

    if obj_changed:
        if obj_created:
            verb = "created"
            obj.created_time = datetime.datetime.now(UTC_TIMEZONE)
        else:
            verb = "changed"
        obj.last_modified_time = datetime.datetime.now(UTC_TIMEZONE)
        if VERBOSITY:
            LOGGER.info("%s %s" % (obj, verb))
        try:
            obj.save()
        except db.utils.DataError as e:
            LOGGER.error("Importing failed for unit entrance {}".format(str(obj)))
            raise e

    syncher.mark(obj, True)
