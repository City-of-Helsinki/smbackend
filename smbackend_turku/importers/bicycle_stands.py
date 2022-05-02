from datetime import datetime

from django.conf import settings

from mobility_data.importers.bicycle_stands import (
    create_bicycle_stand_content_type,
    delete_bicycle_stands as mobility_data_delete_bicycle_stands,
    get_bicycle_stand_objects,
)
from mobility_data.importers.utils import create_mobile_unit_as_unit_reference
from services.management.commands.services_import.services import (
    update_service_node_counts,
)
from services.models import Service, ServiceNode, Unit, UnitServiceDetails
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


class BicycleStandImporter:

    SERVICE_ID = settings.BICYCLE_STANDS_IDS["service"]
    SERVICE_NODE_ID = settings.BICYCLE_STANDS_IDS["service_node"]
    UNITS_ID_OFFSET = settings.BICYCLE_STANDS_IDS["units_offset"]
    SERVICE_NODE_NAME = "Pyöräpysäköinti"
    SERVICE_NAME = "Pyöräpysäköinti"

    SERVICE_NODE_NAMES = {
        "fi": SERVICE_NODE_NAME,
        "sv": "Cykelparkering",
        "en": "Bicycle parking",
    }
    SERVICE_NAMES = {
        "fi": SERVICE_NAME,
        "sv": "Cykelparkering",
        "en": "Bicycle parking",
    }

    def __init__(self, logger=None, root_service_node_name=None, test_data=None):
        self.logger = logger
        self.root_service_node_name = root_service_node_name
        self.test_data = test_data

    def import_bicycle_stands(self):
        service_id = self.SERVICE_ID
        self.logger.info("Importing Bicycle Stands...")
        content_type = create_bicycle_stand_content_type()
        saved_bicycle_stands = 0
        filtered_objects = get_bicycle_stand_objects()
        for i, data_obj in enumerate(filtered_objects):
            unit_id = i + self.UNITS_ID_OFFSET
            obj = Unit(id=unit_id)
            set_field(obj, "location", data_obj.geometry)
            set_tku_translated_field(obj, "name", data_obj.prefix_name)
            set_tku_translated_field(obj, "street_address", data_obj.name)
            extra = {}
            extra["model"] = data_obj.model
            extra["maintained_by_turku"] = data_obj.maintained_by_turku
            extra["number_of_stands"] = data_obj.number_of_stands
            extra["number_of_places"] = data_obj.number_of_places
            extra["hull_lockable"] = data_obj.hull_lockable
            extra["covered"] = data_obj.covered
            # Add non prefixed names to extra, so that the front end does not need
            # to remove the prefix.
            extra["name_fi"] = data_obj.name["fi"]
            extra["name_sv"] = data_obj.name["sv"]
            extra["name_en"] = data_obj.name["en"]
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
            set_service_names_field(obj)
            obj.save()
            create_mobile_unit_as_unit_reference(unit_id, content_type)
            saved_bicycle_stands += 1
        update_service_node_counts()


def delete_bicycle_stands(**kwargs):
    importer = BicycleStandImporter(**kwargs)
    delete_external_source(
        importer.SERVICE_ID,
        importer.SERVICE_NODE_ID,
        mobility_data_delete_bicycle_stands,
    )


def import_bicycle_stands(**kwargs):
    importer = BicycleStandImporter(**kwargs)
    # Delete all Bicycle stand units before storing, to ensure stored data is up to date.
    delete_external_source(
        importer.SERVICE_ID,
        importer.SERVICE_NODE_ID,
        mobility_data_delete_bicycle_stands,
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
    importer.import_bicycle_stands()
