from datetime import datetime
import re
import pytz
from munigeo.importer.sync import ModelSyncher
from services.models import ServiceNode, Service
from services.management.commands.services_import.keyword import KeywordHandler
from .utils import pk_get, save_translated_field

UTC_TIMEZONE = pytz.timezone('UTC')
SERVICE_REFERENCE_SEPARATOR = re.compile('[^0-9]+')


def import_services(syncher=None, noop=False, logger=None, importer=None,
                    ontologytrees=pk_get('ontologytree'),
                    ontologywords=pk_get('ontologyword')):

    nodesyncher = ModelSyncher(ServiceNode.objects.all(), lambda obj: obj.id)
    servicesyncher = ModelSyncher(Service.objects.all(), lambda obj: obj.id)

    def save_object(obj):
        if obj._changed:
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
            if importer:
                importer.services_changed = True

    def _build_servicetree(ontologytrees):
        tree = [ot for ot in ontologytrees if not ot.get('parent_id')]
        for parent_ot in tree:
            _add_ot_children(parent_ot, ontologytrees)

        return tree

    def _add_ot_children(parent_ot, ontologytrees):
        parent_ot['children'] = [ot for ot in ontologytrees if
                                 ot.get('parent_id') == parent_ot['id']]

        for child_ot in parent_ot['children']:
            _add_ot_children(child_ot, ontologytrees)

    def handle_service_node(d, keyword_handler):
        obj = nodesyncher.get(d['id'])
        if not obj:
            obj = ServiceNode(id=d['id'])
            obj._changed = True
        if save_translated_field(obj, 'name', d, 'name'):
            obj._changed = True

        if 'parent_id' in d:
            parent = nodesyncher.get(d['parent_id'])
            assert parent
        else:
            parent = None
        if obj.parent != parent:
            obj.parent = parent
            obj._changed = True
        related_services_changed = False
        if obj.service_reference != d.get('ontologyword_reference', None):
            obj.service_reference = d.get('ontologyword_reference')
            related_services_changed = True
            obj._changed = True

        obj._changed |= update_object_unit_count(obj)
        save_object(obj)
        obj._changed = keyword_handler.sync_searchwords(obj, d, obj._changed)
        save_object(obj)

        nodesyncher.mark(obj)

        if ((related_services_changed or obj.related_services.count() == 0) and
                obj.service_reference is not None):
            related_service_ids = set(
                (id for id in SERVICE_REFERENCE_SEPARATOR.split(obj.service_reference)))
            obj.related_services.set(related_service_ids)

        for child_node in d['children']:
            handle_service_node(child_node, keyword_handler)

    def update_object_unit_count(obj):
        unit_count = obj.get_unit_count()
        if obj.unit_count != unit_count:
            obj.unit_count = unit_count
            return True
        return False

    def handle_service(d, keyword_handler):
        obj = servicesyncher.get(d['id'])
        if not obj:
            obj = Service(id=d['id'])
            obj._changed = True

        obj._changed |= save_translated_field(obj, 'name', d, 'ontologyword')

        period_enabled = d['can_add_schoolyear']
        clarification_enabled = d['can_add_clarification']
        obj._changed |= period_enabled != obj.period_enabled
        obj._changed |= clarification_enabled != obj.clarification_enabled
        obj.period_enabled = period_enabled
        obj.clarification_enabled = clarification_enabled

        obj._changed = keyword_handler.sync_searchwords(obj, d, obj._changed)

        if obj._changed:
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
            if importer:
                importer.services_changed = True
        servicesyncher.mark(obj)

        return obj

    tree = _build_servicetree(ontologytrees)
    keyword_handler = KeywordHandler(logger=logger)
    for d in tree:
        handle_service_node(d, keyword_handler)

    nodesyncher.finish()

    for d in ontologywords:
        handle_service(d, keyword_handler)

    servicesyncher.finish()
