import uuid
from datetime import datetime

from django import db
from munigeo.importer.sync import ModelSyncher

from ptv.models import ServicePTVIdentifier
from ptv.utils import (
    create_available_id,
    get_ptv_resource,
    TKU_PTV_NODE_MAPPING,
    UTC_TIMEZONE,
)
from services.management.commands.services_import.services import (
    update_service_counts,
    update_service_node_counts,
    update_service_root_service_nodes,
)
from services.models import Service, ServiceNode, Unit


class PTVServiceImporter:
    def __init__(self, area_code, logger=None):
        self.service_syncher = ModelSyncher(
            Service.objects.filter(ptv_ids__isnull=False), lambda obj: obj.id
        )
        self.service_id_syncher = ModelSyncher(
            ServicePTVIdentifier.objects.all(), lambda obj: obj.id
        )
        self.are_code = area_code
        self.logger = logger

    @db.transaction.atomic
    def import_services(self):
        data = get_ptv_resource(self.are_code, "service")
        page_count = data["pageCount"]
        for page in range(1, page_count + 1):
            if page > 1:
                data = get_ptv_resource(
                    self.are_code, resource_name="service", page=page
                )
            self._import_services(data)

        self._clean_services()
        update_service_counts()

    def _import_services(self, data):
        id_counter = 1
        for service in data["itemList"]:
            self._handle_service(service, id_counter)
            id_counter += 1

    def _handle_service(self, service_data, id_counter):
        uuid_id = uuid.UUID(service_data.get("id"))
        id_obj = self.service_id_syncher.get(uuid_id)
        # Only import services related to the imported units, therefore their ids should be found.
        if not id_obj:
            return

        if id_obj.service:
            service_id = id_obj.service.id
        else:
            # Check if service with the same name already exists
            service_name = next(
                (
                    item
                    for item in service_data.get("serviceNames")
                    if item["language"] == "fi"
                )
            )
            service_obj = Service.objects.filter(name=service_name.get("value")).first()
            if service_obj:
                service_id = service_obj.id
            else:
                service_id = create_available_id(Service, id_counter)

        service_obj = self.service_syncher.get(service_id)
        if not service_obj:
            service_obj = Service(
                id=service_id, clarification_enabled=False, period_enabled=False
            )
            service_obj._changed = True
            self._handle_service_names(service_data, service_obj)

        if not id_obj.service:
            id_obj.service = service_obj
            id_obj._changed = True
            self._save_object(id_obj)

        self._save_object(service_obj)
        self._handle_units(service_data, service_obj)
        self._handle_service_nodes(service_data, service_obj)

    def _handle_service_names(self, service_data, service_obj):
        for name in service_data.get("serviceNames"):
            lang = name.get("language")
            value = name.get("value")
            obj_key = "{}_{}".format("name", lang)
            setattr(service_obj, obj_key, value)

    def _handle_units(self, service_data, service_obj):
        for channel in service_data.get("serviceChannels"):
            unit_uuid = uuid.UUID(channel.get("serviceChannel").get("id"))
            try:
                unit_obj = Unit.objects.get(ptv_id__id=unit_uuid)
                service_obj.units.add(unit_obj)
                unit_obj.root_service_nodes = ",".join(
                    str(x) for x in unit_obj.get_root_service_nodes()
                )
                unit_obj._changed = True
                self._save_object(unit_obj)

            except Unit.DoesNotExist:
                continue

    def _handle_service_nodes(self, service_data, service_obj):
        for service_class in service_data.get("serviceClasses"):
            self._handle_service_node(service_class, service_obj)
        update_service_node_counts()
        update_service_root_service_nodes()

    def _handle_service_node(self, node, service_obj):
        for name in node.get("name"):
            if name.get("language") == "fi":
                value = name.get("value")
                # TODO: Alternative solution to the Turku mapping
                if value in TKU_PTV_NODE_MAPPING:
                    value_list = TKU_PTV_NODE_MAPPING.get(value)
                    for node_name in value_list:
                        node_obj = ServiceNode.objects.filter(name=node_name).first()
                        if not node_obj:
                            # TODO: What to do with the nodes that can't be mapped to the existing ones.
                            self.logger.warning(
                                'ServiceNode "{}" does not exist!'.format(node_name)
                            )
                            break

                        node_obj.related_services.add(service_obj)
                        node_obj.units.add(*service_obj.units.all())
                        node_obj._changed = True
                        self._save_object(node_obj)

    def _clean_services(self):
        Service.objects.filter(units__isnull=True, ptv_ids__isnull=False).delete()

    def _save_object(self, obj):
        if obj._changed:
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
