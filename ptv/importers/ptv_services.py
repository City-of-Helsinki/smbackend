import uuid
from datetime import datetime

from django import db
from django.db.models import Max
from munigeo.importer.sync import ModelSyncher

from ptv.models import ServicePTVIdentifier
from ptv.utils import get_ptv_resource, UTC_TIMEZONE
from services.models import Service


class PTVServiceImporter:
    service_syncher = ModelSyncher(
        Service.objects.filter(ptv_id__isnull=False), lambda obj: obj.id
    )
    service_id_syncher = ModelSyncher(
        ServicePTVIdentifier.objects.all(), lambda obj: obj.id
    )

    def __init__(self, area_code):
        self.are_code = area_code

    @db.transaction.atomic
    def import_services(self):
        self._import_services()

    def _import_services(self):
        data = get_ptv_resource(self.are_code, "service")
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
            # Create an id by getting next available id since AutoField is not in use.
            service_id = (
                Service.objects.aggregate(Max("id"))["id__max"] or 0
            ) + id_counter

        service_obj = self.service_syncher.get(service_id)
        if not service_obj:
            service_obj = Service(
                id=service_id, clarification_enabled=False, period_enabled=False
            )
            service_obj._changed = True

        if not id_obj.service:
            id_obj.service = service_obj
            id_obj._changed = True
            self._save_object(id_obj)

        self._handle_service_names(service_data, service_obj)
        self._save_object(service_obj)

    def _handle_service_names(self, service_data, service_obj):
        for name in service_data.get("serviceNames"):
            lang = name.get("language")
            value = name.get("value")
            obj_key = "{}_{}".format("name", lang)
            setattr(service_obj, obj_key, value)

    def _save_object(self, obj):
        if obj._changed:
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
