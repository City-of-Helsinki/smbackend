from django.core.management import BaseCommand

from services.management.commands.services_import.services import (
    update_service_counts,
    update_service_node_counts,
)
from services.models import Service, ServiceNode, Unit

SERVICE_NODE = "service_node"
SERVICE = "service"

GAS_FILLING_STATIONS_IDS = {SERVICE_NODE: 20000, SERVICE: 20000}
CHARGING_STATIONS_IDS = {SERVICE_NODE: 30000, SERVICE: 30000}
BICYCLE_STANDS_IDS = {SERVICE_NODE: 40000, SERVICE: 40000}
BIKE_SERVICE_STATIONS_IDS = {SERVICE_NODE: 50000, SERVICE: 50000}

DELETE = [
    GAS_FILLING_STATIONS_IDS,
    CHARGING_STATIONS_IDS,
    BICYCLE_STANDS_IDS,
    BIKE_SERVICE_STATIONS_IDS,
]


# This is a hack script to delete obsolete data as the IDs
# changed. The bug that caused this is fixed and after this is run the
# script is obsolete.
class Command(BaseCommand):
    def handle(self, *args, **options):
        for ids in DELETE:
            Unit.objects.filter(services__id=ids[SERVICE]).delete()
            Service.objects.filter(id=ids[SERVICE]).delete()
            ServiceNode.objects.filter(id=ids[SERVICE_NODE]).delete()
        update_service_node_counts()
        update_service_counts()
