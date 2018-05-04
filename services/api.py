import re
import logging
import uuid

from django.http import Http404
from django.conf import settings
from django.utils import translation
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.contrib.gis.gdal import SpatialReference
from django.shortcuts import get_object_or_404
from modeltranslation.translator import translator, NotRegistered
from rest_framework import serializers, viewsets, generics
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from django.core.exceptions import ValidationError

from haystack.query import SearchQuerySet, SQ
from haystack.inputs import AutoQuery

from mptt.utils import drilldown_tree_for_node

from services.models import Unit, Department, Service
from services.models import ServiceNode, UnitConnection, UnitServiceDetails
from services.models import UnitIdentifier, UnitAlias, UnitAccessibilityProperty
from services.models.unit_connection import SECTION_TYPES
from services.models.unit import PROVIDER_TYPES, ORGANIZER_TYPES, CONTRACT_TYPES
from services.accessibility import RULES as accessibility_rules
from munigeo.models import AdministrativeDivision, Municipality, Address
from munigeo import api as munigeo_api

from rest_framework import renderers
from django.template.loader import render_to_string
from django.utils.module_loading import import_string

from django_filters.rest_framework import DjangoFilterBackend

if settings.REST_FRAMEWORK and settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']:
    DEFAULT_RENDERERS = [import_string(renderer_module)
                         for renderer_module
                         in settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']]
else:
    DEFAULT_RENDERERS = ()

# This allows us to find a serializer for Haystack search results
serializers_by_model = {}

all_views = []


def register_view(klass, name, base_name=None):
    entry = {'class': klass, 'name': name}
    if base_name is not None:
        entry['base_name'] = base_name
    all_views.append(entry)

    if (klass.serializer_class and
            hasattr(klass.serializer_class, 'Meta') and
            hasattr(klass.serializer_class.Meta, 'model')):
        model = klass.serializer_class.Meta.model
        serializers_by_model[model] = klass.serializer_class


LANGUAGES = [x[0] for x in settings.LANGUAGES]

logger = logging.getLogger(__name__)


class MPTTModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(MPTTModelSerializer, self).__init__(*args, **kwargs)
        for field_name in 'lft', 'rght', 'tree_id':
            if field_name in self.fields:
                del self.fields[field_name]


class TranslatedModelSerializer(object):
    def __init__(self, *args, **kwargs):
        super(TranslatedModelSerializer, self).__init__(*args, **kwargs)
        model = self.Meta.model
        try:
            trans_opts = translator.get_options_for_model(model)
        except NotRegistered:
            self.translated_fields = []
            return

        self.translated_fields = trans_opts.fields.keys()
        # Remove the pre-existing data in the bundle.
        for field_name in self.translated_fields:
            for lang in LANGUAGES:
                key = "%s_%s" % (field_name, lang)
                if key in self.fields:
                    del self.fields[key]

    def to_internal_value(self, data):
        """
        Convert complex translated json objects to flat format.
        E.g. json structure containing `name` key like this:
        {
            "name": {
                "fi": "musiikkiklubit",
                "sv": "musikklubbar",
                "en": "music clubs"
            },
            ...
        }
        Transforms this:
        {
            "name": "musiikkiklubit",
            "name_fi": "musiikkiklubit",
            "name_sv": "musikklubbar",
            "name_en": "music clubs"
            ...
        }
        :param data:
        :return:
        """

        extra_fields = {}  # will contain the transformation result
        for field_name in self.translated_fields:
            obj = data.get(field_name, None)  # { "fi": "musiikkiklubit", "sv": ... }
            if not obj:
                continue
            if not isinstance(obj, dict):
                raise ValidationError({field_name: 'This field is a translated field. Instead of a string,'
                                                   ' you must supply an object with strings corresponding'
                                                   ' to desired language ids.'})
            for language in (lang[0] for lang in settings.LANGUAGES if lang[0] in obj):
                value = obj[language]  # "musiikkiklubit"
                if language == settings.LANGUAGES[0][0]:  # default language
                    extra_fields[field_name] = value  # { "name": "musiikkiklubit" }
                extra_fields['{}_{}'.format(field_name, language)] = value  # { "name_fi": "musiikkiklubit" }
            del data[field_name]  # delete original translated fields

        # handle other than translated fields
        data = super().to_internal_value(data)

        # add translated fields to the final result
        data.update(extra_fields)

        return data

    def add_keywords(self, obj, ret):
        kw_dict = {}
        for kw in obj.keywords.all():
            if kw.language not in kw_dict:
                kw_dict[kw.language] = []
            kw_dict[kw.language].append(kw.name)
        ret['keywords'] = kw_dict

    def to_representation(self, obj):
        ret = super(TranslatedModelSerializer, self).to_representation(obj)
        if obj is None:
            return ret

        if 'keywords' in ret:
            self.add_keywords(obj, ret)

        for field_name in self.translated_fields:
            if field_name not in self.fields:
                continue

            d = {}
            for lang in LANGUAGES:
                key = "%s_%s" % (field_name, lang)
                val = getattr(obj, key, None)
                if val is None:
                    continue
                d[lang] = val

            # If no text provided, leave the field as null
            for key, val in d.items():
                if val is not None:
                    break
            else:
                d = None
            ret[field_name] = d
        return ret




def root_services(services):
    tree_ids = set(s.tree_id for s in services)
    return map(lambda x: x.id,
               Service.objects.filter(level=0).filter(
                   tree_id__in=tree_ids))


def root_service_nodes(services):
    # check this
    tree_ids = set(s.tree_id for s in services)
    return map(lambda x: x.id,
               ServiceNode.objects.filter(level=0).filter(
                   tree_id__in=tree_ids))


class JSONAPISerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(JSONAPISerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', {})
        if 'only' in context:
            self.keep_fields = set(context['only'] + ['id'])
            for field_name in list(self.fields.keys()):
                if field_name in self.keep_fields:
                    continue
                del self.fields[field_name]

    def to_representation(self, obj):
        ret = super(JSONAPISerializer, self).to_representation(obj)
        include_fields = self.context.get('include', [])
        if 'municipality' in include_fields and obj.municipality:
            muni_json = munigeo_api.MunicipalitySerializer(obj.municipality, context=self.context).data
            ret['municipality'] = muni_json
        return ret


class DepartmentSerializer(TranslatedModelSerializer, MPTTModelSerializer, JSONAPISerializer):
    id = serializers.SerializerMethodField('get_uuid')
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Department
        exclude = ['uuid', ]

    def get_uuid(self, obj):
            return obj.uuid

    def get_parent(self, obj):
        parent = getattr(obj, 'parent')
        if parent is not None:
            return parent.uuid
        return None


class ServiceNodeSerializer(TranslatedModelSerializer, MPTTModelSerializer, JSONAPISerializer):
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super(ServiceNodeSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        ret = super(ServiceNodeSerializer, self).to_representation(obj)
        include_fields = self.context.get('include', [])
        if 'ancestors' in include_fields:
            ancestors = obj.get_ancestors(ascending=True)
            ser = ServiceNodeSerializer(ancestors, many=True, context={'only': ['name']})
            ret['ancestors'] = ser.data
        only_fields = self.context.get('only', [])
        if 'parent' in only_fields:
            ret['parent'] = obj.parent_id
        ret['period_enabled'] = obj.period_enabled()
        ret['root'] = self.root_service_nodes(obj)
        return ret

    def root_service_nodes(self, obj):
        return next(root_service_nodes([obj]))

    class Meta:
        model = ServiceNode
        fields = '__all__'


class ServiceSerializer(TranslatedModelSerializer, JSONAPISerializer):
    # children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = Service
        fields = ['name', 'id', 'unit_count', 'period_enabled', 'clarification_enabled', 'keywords']


class ServiceDetailsSerializer(TranslatedModelSerializer, JSONAPISerializer):
    def to_representation(self, obj):
        ret = super(ServiceDetailsSerializer, self).to_representation(obj)
        ret['name'] = ServiceSerializer(obj.service).data['name']
        if ret['period_begin_year'] is not None:
            ret['period'] = [ret['period_begin_year'], ret.get('period_end_year')]
        else:
            ret['period'] = None
        del ret['period_begin_year']
        del ret['period_end_year']
        return ret

    class Meta:
        model = UnitServiceDetails
        fields = ['service', 'clarification', 'period_begin_year', 'period_end_year']


class JSONAPIViewSetMixin:
    def initial(self, request, *args, **kwargs):
        ret = super(JSONAPIViewSetMixin, self).initial(request, *args, **kwargs)

        include = self.request.query_params.get('include', '')
        self.include_fields = [x.strip() for x in include.split(',') if x]

        self.only_fields = None
        only = self.request.query_params.get('only', '')
        include_geometry = self.request.query_params.get('geometry', '').lower() in ('true', '1')
        if only:
            self.only_fields = [x.strip() for x in only.split(',') if x]
            if include_geometry:
                self.only_fields.append('geometry')
        return ret

    def get_queryset(self):
        queryset = super(JSONAPIViewSetMixin, self).get_queryset()
        model = queryset.model
        if self.only_fields:
            model_fields = model._meta.get_fields()
            # Verify all field names are valid
            for field_name in self.only_fields:
                for field in model_fields:
                    if field.name == field_name:
                        break
                else:
                    raise ParseError("field '%s' supplied in 'only' not found" % field_name)
            fields = self.only_fields.copy()
            if 'parent' in fields:
                fields.remove('parent')
                fields.append('parent_id')
            queryset = queryset.only(*fields)
        return queryset

    def get_serializer_context(self):
        context = super(JSONAPIViewSetMixin, self).get_serializer_context()

        context['include'] = self.include_fields
        if self.only_fields:
            context['only'] = self.only_fields

        return context


class JSONAPIViewSet(JSONAPIViewSetMixin, viewsets.ReadOnlyModelViewSet):
    pass


class DepartmentViewSet(JSONAPIViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def retrieve(self, request, pk=None):
        try:
            uuid.UUID(pk)
        except ValueError:
            raise Http404

        dept = get_object_or_404(Department, uuid=pk)
        serializer = self.serializer_class(dept, context=self.get_serializer_context())

        include_hierarchy = request.query_params.get('include_hierarchy')
        data = serializer.data
        if (include_hierarchy is not None and
                include_hierarchy.lower() not in ['no', 'false', '0']):
            hierarchy = drilldown_tree_for_node(dept)
            data['hierarchy'] = self.serializer_class(
                hierarchy, many=True, context=self.get_serializer_context()).data

        return Response(data)


register_view(DepartmentViewSet, 'department')


def choicefield_string(choices, key, obj):
    try:
        return next(x[1] for x in choices if getattr(obj, key) == x[0])
    except StopIteration:
        return None


class UnitConnectionSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    section_type = serializers.SerializerMethodField()

    class Meta:
        model = UnitConnection
        fields = '__all__'

    def get_section_type(self, obj):
        return choicefield_string(SECTION_TYPES, 'section_type', obj)


class UnitConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitConnection.objects.all()
    serializer_class = UnitConnectionSerializer

register_view(UnitConnectionViewSet, 'unit_connection')


class UnitAccessibilityPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitAccessibilityProperty
        fields = '__all__'


class UnitAccessibilityPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitAccessibilityProperty.objects.all()
    serializer_class = UnitAccessibilityPropertySerializer


class UnitIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitIdentifier
        exclude = ['unit', 'id']


class ServiceNodeViewSet(JSONAPIViewSet, viewsets.ReadOnlyModelViewSet):
    queryset = ServiceNode.objects.all()
    serializer_class = ServiceNodeSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ['level', 'parent']

    def get_queryset(self):
        queryset = super(ServiceNodeViewSet, self).get_queryset().prefetch_related('related_services')
        args = self.request.query_params
        if 'id' in args:
            id_list = args['id'].split(',')
            queryset = queryset.filter(id__in=id_list)
        if 'ancestor' in args:
            val = args['ancestor']
            queryset = queryset.by_ancestor(val)
        return queryset

register_view(ServiceNodeViewSet, 'service_node')


class ServiceViewSet(JSONAPIViewSet, viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_queryset(self):
        queryset = super(ServiceViewSet, self).get_queryset()
        args = self.request.query_params
        if 'id' in args:
            id_list = args['id'].split(',')
            queryset = queryset.filter(id__in=id_list)
        if 'ancestor' in args:
            val = args['ancestor']
            queryset = queryset.by_ancestor(val)
        return queryset

register_view(ServiceViewSet, 'service')


class UnitSerializer(TranslatedModelSerializer, munigeo_api.GeoModelSerializer,
                     JSONAPISerializer):
    connections = UnitConnectionSerializer(many=True)
    accessibility_properties = UnitAccessibilityPropertySerializer(many=True)
    identifiers = UnitIdentifierSerializer(many=True)
    department = serializers.SerializerMethodField('department_uuid')
    provider_type = serializers.SerializerMethodField()
    organizer_type = serializers.SerializerMethodField()
    contract_type = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(UnitSerializer, self).__init__(*args, **kwargs)
        for f in ('connections', 'accessibility_properties'):
            if f not in self.fields:
                continue
            ser = self.fields[f]
            if 'id' in ser.child.fields:
                del ser.child.fields['id']
            if 'unit' in ser.child.fields:
                del ser.child.fields['unit']

        self._root_node_cache = {}

    def handle_extension_translations(self, extensions):
        if extensions is None or len(extensions) == 0:
            return extensions
        result = {}
        for key, value in extensions.items():
            translations = {}
            if value is None or value == 'None':
                result[key] = None
                continue
            for lang in LANGUAGES:
                with translation.override(lang):
                    translated_value = translation.ugettext(value)
                    if translated_value != value:
                        translations[lang] = translated_value
                    translated_value = None
            if len(translations) > 0:
                result[key] = translations
            else:
                result[key] = value
        return result

    def department_uuid(self, obj):
        if obj.department is not None:
            return obj.department.uuid
        return None

    def get_provider_type(self, obj):
        return choicefield_string(PROVIDER_TYPES, 'provider_type', obj)

    def get_organizer_type(self, obj):
        return choicefield_string(ORGANIZER_TYPES, 'organizer_type', obj)

    def get_contract_type(self, obj):
        key = choicefield_string(CONTRACT_TYPES, 'contract_type', obj)
        if not key:
            return None
        translations = {}
        for lang in LANGUAGES:
            with translation.override(lang):
                translations[lang] = translation.ugettext(key)
        return {
            'id': key,
            'description': translations
        }

    def to_representation(self, obj):
        ret = super(UnitSerializer, self).to_representation(obj)
        if hasattr(obj, 'distance') and obj.distance:
            ret['distance'] = obj.distance.m

        if 'root_service_nodes' in ret:
            if obj.root_service_nodes is None or obj.root_service_nodes == '':
                ret['root_service_nodes'] = None
            else:
                ret['root_service_nodes'] = [int(x) for x in obj.root_service_nodes.split(',')]

        include_fields = self.context.get('include', [])
        if 'department' in include_fields:
            dep_json = DepartmentSerializer(obj.department, context=self.context).data
            ret['department'] = dep_json
        # Not using actual serializer instances below is a performance optimization.
        if 'services' in include_fields:
            services_json = []
            for s in obj.service_nodes.all():
                # Optimization:
                # Store root nodes by tree_id in a dict because otherwise
                # this would generate multiple db queries for every single unit
                tree_id = s._mpttfield('tree_id')  # Forget your privacy!
                root_node = self._root_node_cache.get(tree_id)
                if root_node is None:
                    root_node = s.get_root()
                    self._root_node_cache[tree_id] = root_node

                name = {}
                for lang in LANGUAGES:
                    name[lang] = getattr(s, 'name_{0}'.format(lang))
                data = {
                    'id': s.id,
                    'name': name,
                    'root': root_node.id,
                    'service_reference': s.service_reference
                }
                # if s.identical_to:
                #    data['identical_to'] = getattr(s.identical_to, 'id', None)
                if s.level is not None:
                    data['level'] = s.level
                services_json.append(data)
            ret['services'] = services_json
        if 'accessibility_properties' in include_fields:
            acc_props = [{'variable': s.variable_id, 'value': s.value}
                         for s in obj.accessibility_properties.all()]
            ret['accessibility_properties'] = acc_props

        if 'connections' in include_fields:
            ret['connections'] = UnitConnectionSerializer(obj.connections, many=True).data

        if 'request' not in self.context:
            return ret
        qparams = self.context['request'].query_params
        if qparams.get('geometry', '').lower() in ('true', '1'):
            geom = obj.geometry  # TODO: different geom types
            if geom and obj.geometry != obj.location:
                ret['geometry'] = munigeo_api.geom_to_json(geom, self.srs)
        elif 'geometry' in ret:
            del ret['geometry']

        if self.context.get('service_details'):
            ret['service_details'] = (
                ServiceDetailsSerializer(obj.service_details, many=True).data)

        if 'extensions' in ret:
            ret['extensions'] = self.handle_extension_translations(ret['extensions'])

        def rename_field(src, dest):
            if src in ret:
                ret[dest] = ret[src]
                del ret[src]

        rename_field('desc', 'description')
        rename_field('short_desc', 'short_description')
        return ret

    class Meta:
        model = Unit
        exclude = [
            'connection_hash',
            'service_details_hash',
            'accessibility_property_hash',
            'identifier_hash'
        ]


def make_muni_ocd_id(name, rest=None):
    s = 'ocd-division/country:%s/%s:%s' % (settings.DEFAULT_COUNTRY, settings.DEFAULT_OCD_MUNICIPALITY, name)
    if rest:
        s += '/' + rest
    return s


def get_fields(place, lang_code, fields):
    for field in fields:
        p = place[field]
        if p and lang_code in p:
            place[field] = p[lang_code]
        else:
            place[field] = ''
    return place


class KmlRenderer(renderers.BaseRenderer):
    media_type = 'application/vnd.google-earth.kml+xml'
    format = 'kml'

    def render(self, data, media_type=None, renderer_context=None):
        resp = {}
        lang_code = renderer_context['view'].request.query_params.get('language', LANGUAGES[0])
        if lang_code not in LANGUAGES:
            raise ParseError("Invalid language supplied. Supported languages: %s" %
                             ','.join(LANGUAGES))
        resp['lang_code'] = lang_code
        places = data.get('results', [data])
        resp['places'] = [get_fields(place, lang_code, settings.KML_TRANSLATABLE_FIELDS) for place in places]
        return render_to_string('kml.xml', resp)


class UnitViewSet(munigeo_api.GeoModelAPIView, JSONAPIViewSet, viewsets.ReadOnlyModelViewSet):
    queryset = Unit.objects.filter(public=True)
    serializer_class = UnitSerializer
    renderer_classes = DEFAULT_RENDERERS + [KmlRenderer]
    filter_backends = (DjangoFilterBackend,)

    def __init__(self, *args, **kwargs):
        super(UnitViewSet, self).__init__(*args, **kwargs)
        self.service_details = False

    def get_serializer_context(self):
        ret = super(UnitViewSet, self).get_serializer_context()
        ret['srs'] = self.srs
        ret['service_details'] = self._service_details_requested()
        return ret

    def _service_details_requested(self):
        return self.request.query_params.get('service_details', '').lower() in ('true', '1')

    def get_queryset(self):
        queryset = super(UnitViewSet, self).get_queryset()
        if self._service_details_requested():
            queryset = queryset.prefetch_related('service_details')
            queryset = queryset.prefetch_related('service_details__service')

        filters = self.request.query_params
        if 'id' in filters:
            id_list = filters['id'].split(',')
            queryset = queryset.filter(id__in=id_list)

        if 'municipality' in filters:
            val = filters['municipality'].lower().strip()
            if len(val) > 0:
                municipalities = val.split(',')
                muni_sq = Q()
                for municipality_raw in municipalities:
                    municipality = municipality_raw.strip()
                    if municipality.startswith('ocd-division'):
                        ocd_id = municipality
                    else:
                        ocd_id = make_muni_ocd_id(municipality)
                    try:
                        muni = Municipality.objects.get(division__ocd_id=ocd_id)
                        muni_sq |= Q(municipality=muni)
                    except Municipality.DoesNotExist:
                        raise ParseError("municipality with ID '%s' not found" % ocd_id)

                queryset = queryset.filter(muni_sq)

        if 'provider_type' in filters:
            val = filters.get('provider_type')
            pr_ids = val.split(',')
            queryset = queryset.filter(provider_type__in=pr_ids)

        if 'provider_type__not' in filters:
            val = filters.get('provider_type__not')
            pr_ids = val.split('.')
            queryset = queryset.exclude(provider_type__in=pr_ids)

        level = filters.get('level', None)
        level_specs = None
        if level:
            if level != 'all':
                level_specs = settings.LEVELS.get(level)

        def service_nodes_by_ancestors(service_node_ids):
            srv_list = set()
            for srv_id in service_node_ids:
                srv_list |= set(ServiceNode.objects.all().by_ancestor(srv_id).values_list('id', flat=True))
                srv_list.add(int(srv_id))
            return list(srv_list)

        service_nodes = filters.get('service_node', None)

        service_node_ids = None
        if service_nodes:
            service_nodes = service_nodes.lower()
            service_node_ids = service_nodes.split(',')
        elif level_specs:
            if level_specs['type'] == 'include':
                service_node_ids = level_specs['service_nodes']
        if service_node_ids:
            queryset = queryset.filter(service_nodes__in=service_nodes_by_ancestors(service_node_ids)).distinct()

        service_node_ids = None
        val = filters.get('exclude_service_nodes', None)
        if val:
            val = val.lower()
            service_node_ids = val.split(',')
        elif level_specs:
            if level_specs['type'] == 'exclude':
                service_node_ids = level_specs['service_nodes']
        if service_node_ids:
            queryset = queryset.exclude(service_nodes__in=service_nodes_by_ancestors(service_node_ids)).distinct()

        if 'division' in filters:
            # Divisions can be specified with form:
            # division=helsinki/kaupunginosa:kallio,vantaa/äänestysalue:5
            d_list = filters['division'].lower().split(',')
            div_list = []
            for division_path in d_list:
                if division_path.startswith('ocd-division'):
                    muni_ocd_id = division_path
                else:
                    ocd_id_base = r'[\w0-9~_.-]+'
                    match_re = r'(%s)/([\w_-]+):(%s)' % (ocd_id_base, ocd_id_base)
                    m = re.match(match_re, division_path, re.U)
                    if not m:
                        raise ParseError("'division' must be of form 'muni/type:id'")

                    arr = division_path.split('/')
                    muni_ocd_id = make_muni_ocd_id(arr.pop(0), '/'.join(arr))
                try:
                    div = AdministrativeDivision.objects.select_related('geometry').get(ocd_id=muni_ocd_id)
                except AdministrativeDivision.DoesNotExist:
                    raise ParseError("administrative division with OCD ID '%s' not found" % muni_ocd_id)
                div_list.append(div)

            if div_list:
                mp = div_list.pop(0).geometry.boundary
                for div in div_list:
                    mp += div.geometry.boundary

            queryset = queryset.filter(location__within=mp)

        if 'lat' in filters and 'lon' in filters:
            try:
                lat = float(filters['lat'])
                lon = float(filters['lon'])
            except ValueError:
                raise ParseError("'lat' and 'lon' need to be floating point numbers")
            point = Point(lon, lat, srid=4326)

            if 'distance' in filters:
                try:
                    distance = float(filters['distance'])
                    if not distance > 0:
                        raise ValueError()
                except ValueError:
                    raise ParseError("'distance' needs to be a floating point number")
                queryset = queryset.filter(location__distance_lte=(point, distance))
            queryset = queryset.distance(point, field_name='geometry').order_by('distance')

        if 'bbox' in filters:
            val = self.request.query_params.get('bbox', None)
            if 'bbox_srid' in filters:
                ref = SpatialReference(filters.get('bbox_srid', None))
            else:
                ref = self.srs
            if val:
                bbox_filter = munigeo_api.build_bbox_filter(ref, val, 'location')
                bbox_geometry_filter = munigeo_api.build_bbox_filter(ref, val, 'geometry')
                queryset = queryset.filter(Q(**bbox_filter) | Q(**bbox_geometry_filter))

        maintenance_organization = self.request.query_params.get('maintenance_organization')
        if maintenance_organization:
            queryset = queryset.filter(
                Q(extensions__maintenance_organization=maintenance_organization) |
                Q(extensions__additional_maintenance_organization=maintenance_organization))

        if 'observations' in self.include_fields:
            queryset = queryset.prefetch_related(
                'observation_set__property__allowed_values').prefetch_related(
                    'observation_set__value')

        if 'connections' in self.include_fields:
            queryset = queryset.prefetch_related('connections')

        if 'service_nodes' in self.include_fields:
            queryset = queryset.prefetch_related('service_nodes')

        if 'accessibility_properties' in self.include_fields:
            queryset = queryset.prefetch_related('accessibility_properties')

        return queryset

    def _add_content_disposition_header(self, response):
        if isinstance(response.accepted_renderer, KmlRenderer):
            header = "attachment; filename={}".format('palvelukartta.kml')
            response['Content-Disposition'] = header
        return response

    def retrieve(self, request, pk=None):
        try:
            unit = Unit.objects.get(pk=pk, public=True)
        except Unit.DoesNotExist:
            unit_alias = get_object_or_404(UnitAlias, second=pk)
            unit = unit_alias.first
        serializer = self.serializer_class(unit, context=self.get_serializer_context())
        return Response(serializer.data)

    def list(self, request):
        response = super(UnitViewSet, self).list(request)
        response.add_post_render_callback(self._add_content_disposition_header)
        return response

register_view(UnitViewSet, 'unit')


class SearchSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super(SearchSerializer, self).__init__(*args, **kwargs)
        self.serializer_by_model = {}

    def _strip_context(self, context, model):
        if model == Unit:
            key = 'unit'
        else:
            key = 'service_node'
        for spec in ['include', 'only']:
            if spec in context:
                context[spec] = context[spec].get(key, [])
        return context

    def get_result_serializer(self, model, instance):
        ser = self.serializer_by_model.get(model)
        if not ser:
            ser_class = serializers_by_model[model]
            assert model in serializers_by_model, "Serializer for %s not found" % model
            context = self._strip_context(self.context.copy(), model)
            ser = ser_class(context=context, many=False)
            self.serializer_by_model[model] = ser
        # TODO: another way to serialize with new data without
        # costly Serializer instantiation
        ser.instance = instance
        if hasattr(ser, '_data'):
            del ser._data
        return ser

    def to_representation(self, search_result):
        if not search_result or not search_result.model:
            return None
        model = search_result.model
        serializer = self.get_result_serializer(
            model, search_result.object)
        data = serializer.data
        data['object_type'] = model._meta.model_name
        data['score'] = search_result.score
        return data

KML_REGEXP = re.compile(settings.KML_REGEXP)


class SearchViewSet(munigeo_api.GeoModelAPIView, viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = SearchSerializer
    renderer_classes = DEFAULT_RENDERERS + [KmlRenderer]

    queryset = Unit.objects.all()

    def list(self, request, *args, **kwargs):
        # If the incoming language is not specified, go with the default.
        self.lang_code = request.query_params.get('language', LANGUAGES[0])
        if self.lang_code not in LANGUAGES:
            raise ParseError("Invalid language supplied. Supported languages: %s" %
                             ','.join(LANGUAGES))

        specs = {
            'only_fields': self.request.query_params.get('only', None),
            'include_fields': self.request.query_params.get('include', None)
        }
        for key in specs.keys():
            if specs[key]:
                setattr(self, key, {})
                fields = [x.strip().split('.') for x in specs[key].split(',') if x]
                for f in fields:
                    try:
                        getattr(self, key).setdefault(f[0], []).append(f[1])
                    except IndexError:
                        logger.warning("Field '%s' given in unsupported non-dot-format: '%s'" % (key, specs[key]))
            else:
                setattr(self, key, None)

        input_val = request.query_params.get('input', '').strip()
        q_val = request.query_params.get('q', '').strip()
        if not input_val and not q_val:
            raise ParseError("Supply search terms with 'q=' or autocomplete entry with 'input='")
        if input_val and q_val:
            raise ParseError("Supply either 'q' or 'input', not both")

        old_language = translation.get_language()[:2]
        translation.activate(self.lang_code)

        queryset = SearchQuerySet()

        if hasattr(request, 'accepted_media_type') and re.match(KML_REGEXP, request.accepted_media_type):
            queryset = queryset.models(Unit)
            self.only_fields['unit'].extend(['street_address', 'www'])

        if input_val:
            queryset = (
                queryset
                .filter(autosuggest=input_val)
                .filter_or(autosuggest_extra_searchwords=input_val)
                .filter_or(autosuggest_exact__exact=input_val)
            )
        else:
            queryset = (
                queryset
                .filter(text=AutoQuery(q_val))
                .filter_or(extra_searchwords=q_val)
                .filter_or(address=q_val)
            )
        if 'municipality' in request.query_params:
            val = request.query_params['municipality'].lower().strip()
            if len(val) > 0:
                municipalities = val.split(',')
                muni_q_objects = [SQ(municipality=m.strip()) for m in municipalities]
                muni_q = muni_q_objects.pop()
                for q in muni_q_objects:
                    muni_q |= q
                queryset = queryset.filter(
                    SQ(muni_q |
                       SQ(django_ct='services.service_node') |
                       SQ(django_ct='munigeo.address')))

        service = request.query_params.get('service')
        if service:
            services = service.split(',')
            queryset = queryset.filter(django_ct='services.unit').filter(services__in=services)

        models = set()
        types = request.query_params.get('type', '').split(',')
        for t in types:
            if t == 'service_node':
                models.add(ServiceNode)
            elif t == 'unit':
                models.add(Unit)
            elif t == 'address':
                models.add(Address)
        if len(models) > 0:
            queryset = queryset.models(*list(models))

        only = getattr(self, 'only_fields') or {}
        include = getattr(self, 'include_fields') or {}
        Unit.search_objects.only_fields = only.get('unit')
        Unit.search_objects.include_fields = include.get('unit')

        self.object_list = queryset.load_all()

        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        serializer = self.get_serializer(page, many=True)
        resp = self.get_paginated_response(serializer.data)

        translation.activate(old_language)

        return resp

    def get_serializer_context(self):
        context = super(SearchViewSet, self).get_serializer_context()
        if self.only_fields:
            context['only'] = self.only_fields
        if self.include_fields:
            context['include'] = self.include_fields
        return context

register_view(SearchViewSet, 'search', base_name='search')


class AccessibilityRuleView(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = None

    def list(self, request, *args, **kwargs):
        rules, messages = accessibility_rules.get_data()
        return Response({
            'rules': rules,
            'messages': messages})

register_view(AccessibilityRuleView, 'accessibility_rule', base_name='accessibility_rule')


class AdministrativeDivisionSerializer(munigeo_api.AdministrativeDivisionSerializer):
    def to_representation(self, obj):
        ret = super(AdministrativeDivisionSerializer, self).to_representation(obj)

        req = self.context.get('request', None)
        if req:
            unit_include = req.query_params.get('unit_include', None)
        else:
            unit_include = None
        service_point_id = ret['service_point_id']
        if service_point_id and unit_include:
            try:
                unit = Unit.objects.get(id=service_point_id)
            except Unit.DoesNotExist:
                try:
                    unit_alias = UnitAlias.objects.get(second=service_point_id)
                    unit = unit_alias.first
                except UnitAlias.DoesNotExist:
                    unit = None
            if unit:
                ser = UnitSerializer(unit, context={'only': unit_include.split(',')})
                ret['unit'] = ser.data

        return ret


class AdministrativeDivisionViewSet(munigeo_api.AdministrativeDivisionViewSet):
    serializer_class = AdministrativeDivisionSerializer

register_view(AdministrativeDivisionViewSet, 'administrative_division')


class AddressViewSet(munigeo_api.AddressViewSet):
    serializer_class = munigeo_api.AddressSerializer

register_view(AddressViewSet, 'address')
