from datetime import datetime

from django.conf import settings

from mobility_data.importers.bike_service_stations import (
    create_bike_service_station_content_type,
    delete_bike_service_stations as mobility_data_delete_bike_service_stations,
    get_bike_service_station_objects,
)
from mobility_data.importers.utils import create_mobile_unit_as_unit_reference
from services.management.commands.services_import.services import (
    update_service_counts,
    update_service_node_counts,
)
from services.models import Service, ServiceNode, Unit, UnitServiceDetails
from smbackend_turku.importers.constants import (
    BIKE_SERVICE_STATION_SERVICE_NAME,
    BIKE_SERVICE_STATION_SERVICE_NAMES,
    BIKE_SERVICE_STATION_SERVICE_NODE_NAME,
    BIKE_SERVICE_STATION_SERVICE_NODE_NAMES,
)
from smbackend_turku.importers.utils import (
    create_service,
    create_service_node,
    delete_external_source,
    get_municipality,
    set_field,
    set_service_names_field,
    set_syncher_object_field,
    set_tku_translated_field,
    UTC_TIMEZONE,
)


class BikeServiceStationImporter:

    SERVICE_ID = settings.BIKE_SERVICE_STATIONS_IDS["service"]
    SERVICE_NODE_ID = settings.BIKE_SERVICE_STATIONS_IDS["service_node"]
    UNITS_ID_OFFSET = settings.BIKE_SERVICE_STATIONS_IDS["units_offset"]
    SERVICE_NAME = BIKE_SERVICE_STATION_SERVICE_NAME
    SERVICE_NAMES = BIKE_SERVICE_STATION_SERVICE_NAMES
    SERVICE_NODE_NAME = BIKE_SERVICE_STATION_SERVICE_NODE_NAME
    SERVICE_NODE_NAMES = BIKE_SERVICE_STATION_SERVICE_NODE_NAMES

    def __init__(self, logger=None, root_service_node_name=None, test_data=None):
        self.logger = logger
        self.root_service_node_name = root_service_node_name
        self.test_data = test_data

    def import_bike_service_stations(self):
        service_id = self.SERVICE_ID
        self.logger.info("Importing Bike service stations...")
        content_type = create_bike_service_station_content_type()
        saved_bike_service_stations = 0
        filtered_objects = get_bike_service_station_objects(geojson_file=self.test_data)
        for i, data_obj in enumerate(filtered_objects):
            unit_id = i + self.UNITS_ID_OFFSET
            obj = Unit(id=unit_id)
            set_field(obj, "location", data_obj.geometry)
            set_tku_translated_field(obj, "name", data_obj.name)
            set_tku_translated_field(obj, "street_address", data_obj.address)
            set_tku_translated_field(obj, "description", data_obj.description)
            set_field(obj, "extra", data_obj.extra)
            # 1 = self produced
            set_syncher_object_field(obj, "provider_type", 1)
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                self.logger.warning('Service "{}" does not exist!'.format(service_id))
                continue
            UnitServiceDetails.objects.get_or_create(unit=obj, service=service)
            service_nodes = ServiceNode.objects.filter(related_services=service)
            obj.service_nodes.add(*service_nodes)
            set_field(obj, "root_service_nodes", obj.get_root_service_nodes()[0])
            municipality = get_municipality(data_obj.municipality)
            set_field(obj, "municipality", municipality)
            set_field(obj, "address_zip", data_obj.zip_code)

            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            set_service_names_field(obj)
            obj.save()
            create_mobile_unit_as_unit_reference(unit_id, content_type)
            saved_bike_service_stations += 1
        update_service_node_counts()
        update_service_counts()
        self.logger.info(f"Imported {len(filtered_objects)} bike service stations...")


def delete_bike_service_stations(**kwargs):
    importer = BikeServiceStationImporter(**kwargs)
    delete_external_source(
        importer.SERVICE_ID,
        importer.SERVICE_NODE_ID,
        mobility_data_delete_bike_service_stations,
    )
    update_service_node_counts()
    update_service_counts()


def import_bike_service_stations(**kwargs):
    importer = BikeServiceStationImporter(**kwargs)
    # Delete all Bike service station units before storing, to ensure stored data is up to date.
    delete_external_source(
        importer.SERVICE_ID,
        importer.SERVICE_NODE_ID,
        mobility_data_delete_bike_service_stations,
    )
    create_service_node(
        importer.SERVICE_NODE_ID,
        importer.SERVICE_NODE_NAME,
        importer.root_service_node_name,
        importer.SERVICE_NODE_NAMES,
    )
    create_service(
        importer.SERVICE_ID,
        importer.SERVICE_NODE_ID,
        importer.SERVICE_NAME,
        importer.SERVICE_NAMES,
    )
    importer.import_bike_service_stations()
