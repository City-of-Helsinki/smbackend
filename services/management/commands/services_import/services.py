from datetime import datetime
import re
import pytz
from django import db
from munigeo.models import AdministrativeDivision, AdministrativeDivisionType
from munigeo.importer.sync import ModelSyncher
from services.models import ServiceNode, Service, Unit, ServiceNodeUnitCount
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

        save_object(obj)
        obj._changed = keyword_handler.sync_searchwords(obj, d, obj._changed)
        save_object(obj)

        nodesyncher.mark(obj)

        if ((related_services_changed or obj.related_services.count() == 0) and obj.service_reference is not None):
            related_service_ids = set(
                (id for id in SERVICE_REFERENCE_SEPARATOR.split(obj.service_reference)))
            obj.related_services.set(related_service_ids)

        for child_node in d['children']:
            handle_service_node(child_node, keyword_handler)

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


def update_service_node(node, units_by_service):
    units = units_by_service.get(node.id, {})
    for child in node.get_children():
        child_units = update_service_node(child, units_by_service)
        for k, v in child_units.items():
            s = units.get(k, set())
            s.update(v)
            units[k] = s
    node._unit_count = {}
    for k, v in units.items():
        node._unit_count[k] = len(units[k])
    return units


MUNI_DIVISION_TYPE = None
DIVISIONS_BY_MUNI = None


def get_municipality_division_type():
    global MUNI_DIVISION_TYPE
    if MUNI_DIVISION_TYPE is None:
        try:
            MUNI_DIVISION_TYPE = AdministrativeDivisionType.objects.get(type='muni')
        except AdministrativeDivisionType.DoesNotExist:
            MUNI_DIVISION_TYPE = None
    return MUNI_DIVISION_TYPE


def get_divisions_by_muni():
    global DIVISIONS_BY_MUNI
    TYPE = get_municipality_division_type()
    if TYPE is None:
        return {}
    if DIVISIONS_BY_MUNI is None:
        DIVISIONS_BY_MUNI = dict((
            (x.name_fi.lower(), x) for x in
            AdministrativeDivision.objects.filter(type=TYPE)))
    return DIVISIONS_BY_MUNI


def update_count_objects(service_node_unit_count_objects, city_as_department, node):
    """
    This is a generator which yields all the objects that need to be saved.
    (Objects that didn't exist or whose count field was updated.)
    """
    for muni, count in node._unit_count.items():
        obj = service_node_unit_count_objects.get((node.id, muni))
        city_as_department_count = 0
        if muni is not None:
            city_as_department_count = city_as_department.get(node.id, {}).get(muni, 0)
        if obj is None:
            obj = ServiceNodeUnitCount(
                service_node=node,
                division_type=get_municipality_division_type(),
                division=get_divisions_by_muni().get(muni),
                count=count,
                city_as_department=city_as_department_count)
            yield obj
        else:
            if obj.count != count:
                obj.count = count
                yield obj
            if obj.city_as_department != city_as_department_count:
                obj.city_as_department = city_as_department_count
                yield obj

    for node in node.get_children():
        yield from update_count_objects(service_node_unit_count_objects, city_as_department, node)

def update_city_as_department(city_as_department, service_node_unit_counts, node):
    counts = city_as_department.get(node.id, {})
    for child in node.get_children():
        child_counts = update_city_as_department(city_as_department, service_node_unit_counts, child)
        for muni in child_counts.keys():
            counts[muni] = counts.get(muni, 0) + child_counts[muni]
            obj = service_node_unit_counts.get((node.id, muni), None)
            if obj is not None:
                obj.city_as_department = counts[muni]
                obj.save()
    return counts

@db.transaction.atomic
def save_objects(objects):
    for o in objects:
        o.save()


def update_service_node_counts():
    units_by_service = {}
    city_as_department = {}
    through_values = Unit.service_nodes.through.objects.filter(
        unit__public=True).values_list('servicenode_id', 'unit__municipality', 'unit_id',
                                       'unit__root_department__municipality_id').distinct()
    for service_node_id, municipality, unit_id, municipality_id in through_values:
        unit_set = units_by_service.setdefault(service_node_id, {}).setdefault(municipality, set())
        unit_set.add(unit_id)
        units_by_service[service_node_id][municipality] = unit_set

        def add_city_as_department(service_node_id, muni):
            if city_as_department.get(service_node_id, {}).get(muni, 0) == 0:
                service_node_dict = city_as_department.get(service_node_id, {})
                service_node_dict[muni] = 1
                city_as_department[service_node_id] = service_node_dict
            else:
                city_as_department[service_node_id][muni] += 1

        if municipality_id is not None:
            add_city_as_department(service_node_id, municipality_id)
        if municipality != municipality_id:
            add_city_as_department(service_node_id, municipality)

    unit_counts_to_be_updated = set(
        ((service_node_id, municipality) for service_node_id, municipality, _, _ in through_values))

    for c in ServiceNodeUnitCount.objects.select_related('division').all():
        div_name = c.division and c.division.name_fi.lower()
        if (c.service_node_id, div_name) not in unit_counts_to_be_updated:
            c.delete()

    tree = ServiceNode.tree_objects.all().get_cached_trees()
    for node in tree:
        update_service_node(node, units_by_service)

    def count_object_pair(x):
        div = x.division.name_fi.lower() if x.division is not None else None
        return ((x.service_node_id, div), x)

    service_node_unit_count_objects = dict((
        count_object_pair(x) for x in ServiceNodeUnitCount.objects.select_related('division').all()))
    objects_to_save = []
    for node in tree:
        objects_to_save.extend(update_count_objects(service_node_unit_count_objects, city_as_department, node))
        update_city_as_department(city_as_department, service_node_unit_count_objects, node)
    save_objects(objects_to_save)
    return tree


@db.transaction.atomic
def update_service_root_service_nodes():
    tree_roots = dict(ServiceNode.objects.filter(level=0).values_list('tree_id', 'id'))
    service_nodes = ServiceNode.objects.all().prefetch_related('related_services')
    services = set()
    service_roots = dict()
    for node in service_nodes:  # TODO: ordering
        for service in node.related_services.all():
            service_roots[service.id] = tree_roots[node.tree_id]
            services.add(service)
    for service in services:
        service.root_service_node_id = service_roots[service.id]
        service.save(update_fields=['root_service_node'])
