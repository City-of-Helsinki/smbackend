import json
import re

from django.conf import settings
from django.utils import translation
from django.db.models import Q
from django.contrib.gis.geos import Polygon, MultiPolygon, GeometryCollection, Point
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.shortcuts import get_object_or_404
from modeltranslation.translator import translator, NotRegistered
from rest_framework import serializers, viewsets, generics
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from haystack.query import SearchQuerySet, SQ
from haystack.inputs import AutoQuery

from services.models import *
from services.accessibility import RULES as accessibility_rules
from munigeo.models import *
from munigeo import api as munigeo_api

from rest_framework import renderers
from rest_framework_jsonp.renderers import JSONPRenderer
from django.template.loader import render_to_string
from django.utils.module_loading import import_string

if settings.REST_FRAMEWORK and settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']:
    DEFAULT_RENDERERS = [import_string(renderer_module) for renderer_module in settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES']]
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
        hasattr(klass.serializer_class.Meta, 'model')
    ):
        model = klass.serializer_class.Meta.model
        serializers_by_model[model] = klass.serializer_class


LANGUAGES = [x[0] for x in settings.LANGUAGES]

class MPTTModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(MPTTModelSerializer, self).__init__(*args, **kwargs)
        for field_name in 'lft', 'rght', 'tree_id':
            if field_name in self.fields:
                del self.fields[field_name]

class TranslatedModelSerializer(serializers.ModelSerializer):
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

    def to_representation(self, obj):
        ret = super(TranslatedModelSerializer, self).to_representation(obj)
        if obj is None:
            return ret

        for field_name in self.translated_fields:
            if not field_name in self.fields:
                continue
            d = {}
            for lang in LANGUAGES:
                key = "%s_%s" % (field_name, lang)  
                val = getattr(obj, key, None)
                if val == None:
                    continue 
                d[lang] = val

            # If no text provided, leave the field as null
            for key, val in d.items():
                if val != None:
                    break
            else:
                d = None
            ret[field_name] = d

        return ret


class OrganizationSerializer(TranslatedModelSerializer):
    class Meta:
        model = Organization

class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

register_view(OrganizationViewSet, 'organization')


class DepartmentSerializer(TranslatedModelSerializer):
    class Meta:
        model = Department

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

register_view(DepartmentViewSet, 'department')


def root_services(services):
    tree_ids = set(s.tree_id for s in services)
    return map(lambda x: x.id,
               Service.objects.filter(level=0).filter(
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

class ServiceSerializer(TranslatedModelSerializer, MPTTModelSerializer, JSONAPISerializer):
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super(ServiceSerializer, self).__init__(*args, **kwargs)
        keep_fields = getattr(self, 'keep_fields', [])
        if not keep_fields or 'root' in keep_fields:
            self.fields['root'] = serializers.SerializerMethodField('root_services')

    def to_representation(self, obj):
        ret = super(ServiceSerializer, self).to_representation(obj)
        include_fields = self.context.get('include', [])
        if 'ancestors' in include_fields:
            ancestors = obj.get_ancestors(ascending=True)
            ser = ServiceSerializer(ancestors, many=True, context={'only': ['name']})
            ret['ancestors'] = ser.data
        only_fields = self.context.get('only', [])
        if 'parent' in only_fields:
            ret['parent'] = obj.parent_id
        return ret

    def root_services(self, obj):
        return next(root_services([obj]))

    class Meta:
        model = Service


class JSONAPIViewSetMixin:
    def initial(self, request, *args, **kwargs):
        ret = super(JSONAPIViewSetMixin, self).initial(request, *args, **kwargs)

        include = self.request.QUERY_PARAMS.get('include', '')
        self.include_fields = [x.strip() for x in include.split(',') if x]

        only = self.request.QUERY_PARAMS.get('only', '')
        if only:
            self.only_fields = [x.strip() for x in only.split(',') if x]
        else:
            self.only_fields = None

        return ret

    def get_queryset(self):
        queryset = super(JSONAPIViewSetMixin, self).get_queryset()
        model = queryset.model
        if self.only_fields:
            model_fields = model._meta.get_fields()
            #Verify all field names are valid
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

class UnitConnectionSerializer(TranslatedModelSerializer):
    class Meta:
        model = UnitConnection

class UnitConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitConnection.objects.all()
    serializer_class = UnitConnectionSerializer

register_view(UnitConnectionViewSet, 'unit_connection')


class UnitAccessibilityPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitAccessibilityProperty

class UnitAccessibilityPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitAccessibilityProperty.objects.all()
    serializer_class = UnitAccessibilityPropertySerializer


class UnitIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitIdentifier
        exclude = ['unit', 'id']


class ServiceViewSet(JSONAPIViewSet, viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filter_fields = ['level', 'parent']

    def get_queryset(self):
        queryset = super(ServiceViewSet, self).get_queryset()
        args = self.request.QUERY_PARAMS
        if 'id' in args:
            id_list = args['id'].split(',')
            queryset = queryset.filter(id__in=id_list)
        if 'ancestor' in args:
            val = args['ancestor']
            queryset = queryset.by_ancestor(val)
        return queryset

register_view(ServiceViewSet, 'service')


class UnitSerializer(TranslatedModelSerializer, MPTTModelSerializer,
                     munigeo_api.GeoModelSerializer, JSONAPISerializer):
    connections = UnitConnectionSerializer(many=True)
    accessibility_properties = UnitAccessibilityPropertySerializer(many=True)
    identifiers = UnitIdentifierSerializer(many=True)

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

    def to_representation(self, obj):
        ret = super(UnitSerializer, self).to_representation(obj)
        if hasattr(obj, 'distance') and obj.distance:
            ret['distance'] = obj.distance.m

        if 'keywords' in ret:
            kw_dict = {}
            for kw in obj.keywords.all():
                if not kw.language in kw_dict:
                    kw_dict[kw.language] = []
                kw_dict[kw.language].append(kw.name)
            ret['keywords'] = kw_dict

        if 'root_services' in ret:
            if obj.root_services == None or obj.root_services == '':
                ret['root_services'] = None
            else:
                ret['root_services'] = [int(x) for x in obj.root_services.split(',')]

        include_fields = self.context.get('include', [])
        if 'department' in include_fields:
            dep_json = DepartmentSerializer(obj.department, context=self.context).data
            ret['department'] = dep_json
        if 'municipality' in include_fields and obj.municipality:
            muni_json = munigeo_api.MunicipalitySerializer(obj.municipality, context=self.context).data
            ret['municipality'] = muni_json
        # Not using actual serializer instances below is a performance optimization.
        if 'services' in include_fields:
            services_json = []
            for s in obj.services.all():
                name = {}
                for lang in LANGUAGES:
                    name[lang] = getattr(s, 'name_{0}'.format(lang))
                data = {'id': s.id, 'name': name, 'root': s.get_root().id}
                if s.identical_to:
                    data['identical_to'] = getattr(s.identical_to, 'id', None)
                services_json.append(data)
            ret['services'] = services_json
        if 'accessibility_properties' in include_fields:
            acc_props = [{'variable': s.variable_id, 'value': s.value}
                         for s in obj.accessibility_properties.all()]
            ret['accessibility_properties'] = acc_props

        if not 'request' in self.context:
            return ret
        qparams = self.context['request'].query_params
        if qparams.get('geometry', '').lower() in ('true', '1'):
            try:
                geom = obj.geometry.path # TODO: different geom types
                ret['geometry'] = munigeo_api.geom_to_json(geom, self.srs)
            except UnitGeometry.DoesNotExist:
                ret['geometry'] = None
        return ret

    class Meta:
        model = Unit
        exclude = [
            'connection_hash', 'accessibility_property_hash',
            'identifier_hash',
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
    queryset = Unit.objects.prefetch_related('observations__value').prefetch_related('observations__property__allowed_values').prefetch_related('services').all()
    serializer_class = UnitSerializer

    renderer_classes = DEFAULT_RENDERERS + [KmlRenderer]

    def get_serializer_context(self):
        ret = super(UnitViewSet, self).get_serializer_context()
        ret['srs'] = self.srs
        return ret

    def get_queryset(self):
        queryset = super(UnitViewSet, self).get_queryset()
        filters = self.request.QUERY_PARAMS
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

        level = filters.get('level', None)
        level_specs = None
        if level:
            if level != 'all':
                level_specs = settings.LEVELS.get(level)

        def services_by_ancestors(service_ids):
            srv_list = set()
            for srv_id in service_ids:
                srv_list |= set(Service.objects.all().by_ancestor(srv_id).values_list('id', flat=True))
                srv_list.add(int(srv_id))
            return list(srv_list)

        services = filters.get('service', None)
        service_ids = None
        if services:
            services = services.lower()
            service_ids = services.split(',')
        elif level_specs:
            if level_specs['type'] == 'include':
                service_ids = level_specs['services']
        if service_ids:
            queryset = queryset.filter(services__in=services_by_ancestors(service_ids)).distinct()

        service_ids = None
        val = filters.get('exclude_services', None)
        if val:
            val = val.lower()
            service_ids = val.split(',')
        elif level_specs:
            if level_specs['type'] == 'exclude':
                service_ids = level_specs['services']
        if service_ids:
            queryset = queryset.exclude(services__in=services_by_ancestors(service_ids)).distinct()

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

            div_geom = [div.geometry.boundary for div in div_list]
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
            val = self.request.QUERY_PARAMS.get('bbox', None)
            if 'bbox_srid' in filters:
                ref = SpatialReference(filters.get('bbox_srid', None))
            else:
                ref = self.srs
            if val:
                bbox_filter = munigeo_api.build_bbox_filter(ref, val, 'location')
                queryset = queryset.filter(**bbox_filter)

        return queryset

    def _add_content_disposition_header(self, response):
        if isinstance(response.accepted_renderer, KmlRenderer):
            header = "attachment; filename={}".format('palvelukartta.kml')
            response['Content-Disposition'] = header
        return response

    def retrieve(self, request, pk=None):
        queryset = Unit.objects.all()
        try:
            unit = Unit.objects.get(pk=pk)
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
            key = 'service'
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

    def list(self, request, *args, **kwargs):
        # If the incoming language is not specified, go with the default.
        self.lang_code = request.QUERY_PARAMS.get('language', LANGUAGES[0])
        if self.lang_code not in LANGUAGES:
            raise ParseError("Invalid language supplied. Supported languages: %s" %
                             ','.join(LANGUAGES))

        context = {}

        specs = {
            'only_fields': self.request.QUERY_PARAMS.get('only', None),
            'include_fields': self.request.QUERY_PARAMS.get('include', None)
        }
        for key in specs.keys():
            if specs[key]:
                setattr(self, key, {})
                fields = [x.strip().split('.') for x in specs[key].split(',') if x]
                for f in fields:
                    getattr(self, key).setdefault(f[0], []).append(f[1])
            else:
                setattr(self, key, None)

        input_val = request.QUERY_PARAMS.get('input', '').strip()
        q_val = request.QUERY_PARAMS.get('q', '').strip()
        if not input_val and not q_val:
            raise ParseError("Supply search terms with 'q=' or autocomplete entry with 'input='")
        if input_val and q_val:
            raise ParseError("Supply either 'q' or 'input', not both")

        old_language = translation.get_language()[:2]
        translation.activate(self.lang_code)

        queryset = SearchQuerySet()

        if hasattr(request, 'accepted_media_type') and re.match(KML_REGEXP, request.accepted_media_type):
            queryset = queryset.models(Unit)
            self.only_fields['unit'].extend(['street_address', 'www_url'])

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
        if 'municipality' in request.QUERY_PARAMS:
            val = request.QUERY_PARAMS['municipality'].lower().strip()
            if len(val) > 0:
                municipalities = val.split(',')
                muni_q_objects = [SQ(municipality=m.strip()) for m in municipalities]
                muni_q = muni_q_objects.pop()
                for q in muni_q_objects:
                    muni_q |= q
                queryset = queryset.filter(SQ(muni_q | SQ(django_ct='services.service') | SQ(django_ct='munigeo.address')))

        service = request.QUERY_PARAMS.get('service')
        if service:
            services = service.split(',')
            queryset = queryset.filter(django_ct='services.unit').filter(services__in=services)

        models = set()
        types = request.QUERY_PARAMS.get('type', '').split(',')
        for t in types:
            if t == 'service':
                models.add(Service)
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
            unit_include = req.QUERY_PARAMS.get('unit_include', None)
        else:
            unit_include = None
        service_point_id = ret['service_point_id']
        if service_point_id and unit_include:
            params = self.context
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
