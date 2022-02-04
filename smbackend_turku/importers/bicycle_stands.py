from datetime import datetime
from django.conf import settings
from mobility_data.models import content_type
from services.models import (
    Service,
    ServiceNode,
    Unit,
    UnitServiceDetails,
)
from services.management.commands.services_import.services import (
    update_service_node_counts,
)
from smbackend_turku.importers.utils import (
    set_field,
    set_tku_translated_field,
    set_syncher_object_field,
    create_service,
    create_service_node,
    get_municipality,
    UTC_TIMEZONE,
)
from mobility_data.importers.bicycle_stands import (
    get_bicycle_stand_objects,
    delete_bicycle_stands,
    create_bicycle_stand_content_type,
)
from mobility_data.importers.utils import create_mobile_unit_as_unit_reference


class BicycleStandImporter:

    SERVICE_ID = settings.BICYCLE_STANDS_IDS["service"]
    SERVICE_NODE_ID = settings.BICYCLE_STANDS_IDS["service_node"]
    UNITS_ID_OFFSET = settings.BICYCLE_STANDS_IDS["units_offset"]
    SERVICE_NODE_NAME = "Polkupyöräparkit"
    SERVICE_NAME = "Polkupyöräparkki"

    SERVICE_NODE_NAMES = {
        "fi": SERVICE_NODE_NAME,
        "sv": "Cykelställningar",
        "en": "Bicycle stands",
    }
    SERVICE_NAMES = {"fi": SERVICE_NAME, "sv": "Cykelställning", "en": "Bicycle stand"}

    def __init__(self, logger=None, root_service_node_name=None, test_data=None):
        self.logger = logger
        self.root_service_node_name = root_service_node_name
        self.test_data = test_data

    def import_bicycle_stands(self):
        service_id = self.SERVICE_ID
        self.logger.info("Importing Bicycle Stands...")
        # Delete all Bicycle stand units before storing, to ensure stored data is up-to-date.
        Unit.objects.filter(services__id=service_id).delete()
        # Delete from mobility_data
        delete_bicycle_stands()
        # create mobility_data content type
        content_type = create_bicycle_stand_content_type()
        saved_bicycle_stands = 0
        filtered_objects = get_bicycle_stand_objects(xml_data=self.test_data)
        for i, data_obj in enumerate(filtered_objects):
            unit_id = i + self.UNITS_ID_OFFSET
            obj = Unit(id=unit_id)
            set_field(obj, "location", data_obj.geometry)
            set_tku_translated_field(obj, "name", data_obj.name)
            set_tku_translated_field(obj, "street_address", data_obj.name)
            extra = {}
            extra["model"] = data_obj.model
            extra["maintained_by_turku"] = data_obj.maintained_by_turku
            extra["number_of_stands"] = data_obj.number_of_stands
            extra["number_of_places"] = data_obj.number_of_places
            extra["hull_lockable"] = data_obj.hull_lockable
            extra["covered"] = data_obj.covered
            set_field(obj, "extra", extra)
            if data_obj.maintained_by_turku:
                # 1 = self produced
                set_syncher_object_field(obj, "provider_type", 1)
            else:
                # 7 = Unknown production method
                set_syncher_object_field(obj, "provider_type", 7)

            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                self.logger.warning('Service "{}" does not exist!'.format(service_id))
                continue
            UnitServiceDetails.objects.get_or_create(unit=obj, service=service)
            service_nodes = ServiceNode.objects.filter(related_services=service)
            obj.service_nodes.add(*service_nodes)
            set_field(obj, "root_service_nodes", obj.get_root_service_nodes()[0])
            municipality = get_municipality(data_obj.city)
            set_field(obj, "municipality", municipality)
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
            create_mobile_unit_as_unit_reference(unit_id, content_type)
            saved_bicycle_stands += 1
        update_service_node_counts()


def import_bicycle_stands(**kwargs):
    importer = BicycleStandImporter(**kwargs)
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
    importer.import_bicycle_stands()
