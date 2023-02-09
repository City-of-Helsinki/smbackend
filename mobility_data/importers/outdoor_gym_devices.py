import logging

from django import db

from mobility_data.models import MobileUnit
from services.models import Service, Unit

from .utils import delete_mobile_units, get_or_create_content_type

logger = logging.getLogger("mobility_data")
SERVICE_NAME = "Outdoor Gym Devices"
CONTENT_TYPE_NAME = "OutdoorGymDevice"

db.transaction.atomic


def create_content_type():
    description = "Outdoor gym devices in Turku."
    content_type, _ = get_or_create_content_type(CONTENT_TYPE_NAME, description)
    return content_type


db.transaction.atomic


def save_outdoor_gym_devices():
    """
    Save only the ID of the Unit. The data will be serialized
    from the Unit table using this ID.
    """
    delete_mobile_units(CONTENT_TYPE_NAME)
    try:
        service = Service.objects.get(name_en=SERVICE_NAME)
    except Service.DoesNotExist:
        return 0

    content_type = create_content_type()
    units_qs = Unit.objects.filter(services=service)
    for unit in units_qs:
        mobile_unit = MobileUnit.objects.create(unit_id=unit.id)
        mobile_unit.content_types.add(content_type)
        mobile_unit.save()
    return units_qs.count()
