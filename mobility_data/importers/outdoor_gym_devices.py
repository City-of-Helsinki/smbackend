import logging

from services.models import Service, Unit

from .utils import MobileUnitDataBase

logger = logging.getLogger("mobility_data")
SERVICE_NAME = "Outdoor Gym Devices"
CONTENT_TYPE_NAME = "OutdoorGymDevice"


class OutdoorGymDevice(MobileUnitDataBase):
    def __init__(self, unit_id):
        super().__init__()
        self.unit_id = unit_id


def get_oudoor_gym_devices():
    """
    Save only the ID of the Unit. The data will be serialized
    from the Unit table using this ID.
    """
    outdoor_gym_devices = []
    try:
        service = Service.objects.get(name_en=SERVICE_NAME)
    except Service.DoesNotExist:
        return None

    units_qs = Unit.objects.filter(services=service)
    for unit in units_qs:
        outdoor_gym_devices.append(OutdoorGymDevice(unit.id))
    return outdoor_gym_devices
