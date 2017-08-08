from datetime import datetime
import pytz
from munigeo.importer.sync import ModelSyncher
from services.models import OntologyTreeNode, OntologyWord
from services.management.commands.services_import.keyword import KeywordHandler
from .utils import pk_get, save_translated_field

UTC_TIMEZONE = pytz.timezone('UTC')


def import_services(syncher=None, noop=False, logger=None, importer=None,
                    ontologytrees=pk_get('ontologytree'),
                    ontologywords=pk_get('ontologyword')):

    nodesyncher = ModelSyncher(OntologyTreeNode.objects.all(), lambda obj: obj.id)
    servicesyncher = ModelSyncher(OntologyWord.objects.all(), lambda obj: obj.id)

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

    def handle_servicenode(d, keyword_handler):
        obj = nodesyncher.get(d['id'])
        if not obj:
            obj = OntologyTreeNode(id=d['id'])
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
        if obj.ontologyword_reference != d.get('ontologyword_reference', None):
            obj.ontologyword_reference = d.get('ontologyword_reference')
            obj._changed = True

        obj._changed = keyword_handler.sync_searchwords(obj, d, obj._changed)

        # FIXME: this does double work
        unit_count = obj.get_unit_count()
        if obj.unit_count != unit_count:
            obj.unit_count = unit_count
            obj._changed = True

        if obj._changed:
            obj.unit_count = obj.get_unit_count()
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
            if importer:
                importer.services_changed = True
        nodesyncher.mark(obj)

        for child_node in d['children']:
            handle_servicenode(child_node)

    def handle_servicetype(d, keyword_handler):
        obj = servicesyncher.get(d['id'])
        if not obj:
            obj = OntologyWord(id=d['id'])
            obj._changed = True

        if save_translated_field(obj, 'name', d, 'ontologyword'):
            obj._changed = True

        obj._changed = keyword_handler.sync_searchwords(obj, d, obj._changed)

        if obj._changed:
            obj.unit_count = obj.get_unit_count()
            obj.last_modified_time = datetime.now(UTC_TIMEZONE)
            obj.save()
            if importer:
                importer.services_changed = True
        servicesyncher.mark(obj)

        return obj

    tree = _build_servicetree(ontologytrees)
    keyword_handler = KeywordHandler(logger=logger)
    for d in tree:
        handle_servicenode(d, keyword_handler)

    nodesyncher.finish()

    for d in ontologywords:
        handle_servicetype(d, keyword_handler)

    servicesyncher.finish()
