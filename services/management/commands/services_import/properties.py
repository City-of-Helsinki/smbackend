import datetime
import logging

import pytz
from django import db

from services.models import Unit

from .utils import pk_get

UTC_TIMEZONE = pytz.timezone("UTC")
VERBOSITY = True
LOGGER = logging.getLogger(__name__)
CACHED_UNIT = None


def import_unit_properties(fetch_resource=pk_get):
    obj_list = fetch_resource("unit_property")
    for info in sorted(obj_list, key=lambda x: x["unit_id"]):
        _import_unit_property(info.copy())


@db.transaction.atomic
def _import_unit_property(info):
    if info["property_name"] == "lipas.geometry":
        return

    global CACHED_UNIT
    if not CACHED_UNIT or CACHED_UNIT.id != info["unit_id"]:
        try:
            CACHED_UNIT = Unit.objects.get(pk=info["unit_id"])
        except Unit.DoesNotExist:
            if VERBOSITY:
                LOGGER.warning("Unit with id (%d) not found" % info["unit_id"])
            return

    cached_unit_extra = CACHED_UNIT.extra
    property_name = info["property_name"]
    if "value_numeric" in info:
        property_value = info["value_numeric"]
    elif "value_text" in info:
        property_value = info["value_text"]
    else:
        return

    if (
        property_name in cached_unit_extra
        and cached_unit_extra[property_name] == property_value
    ):
        return

    CACHED_UNIT.extra[property_name] = property_value
    CACHED_UNIT.last_modified_time = datetime.datetime.now(UTC_TIMEZONE)
    if VERBOSITY:
        LOGGER.info(
            "%s updated with property: { %s: %s }"
            % (CACHED_UNIT, property_name, property_value)
        )
    try:
        CACHED_UNIT.save()
    except db.utils.DataError as e:
        LOGGER.error("Importing failed for unit attribute {}".format(str(info)))
        raise e
