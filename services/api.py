import json
import re

from django.conf import settings
from django.utils import translation
from django.db.models import Q
from django.contrib.gis.geos import Polygon, MultiPolygon, GeometryCollection, Point
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from modeltranslation.translator import translator, NotRegistered
from rest_framework import serializers, viewsets, generics
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery

from services.models import *
from services.accessibility import RULES as accessibility_rules
from munigeo.models import *
from munigeo import api as munigeo_api


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

class JSONAPIViewSet(viewsets.ReadOnlyModelViewSet):
    def initial(self, request, *args, **kwargs):
        ret = super(JSONAPIViewSet, self).initial(request, *args, **kwargs)

        include = self.request.QUERY_PARAMS.get('include', '')
        self.include_fields = [x.strip() for x in include.split(',') if x]

        only = self.request.QUERY_PARAMS.get('only', '')
        if only:
            self.only_fields = [x.strip() for x in only.split(',') if x]
        else:
            self.only_fields = None

        return ret

    def get_queryset(self):
        queryset = super(JSONAPIViewSet, self).get_queryset()
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
        context = super(JSONAPIViewSet, self).get_serializer_context()

        context['include'] = self.include_fields
        if self.only_fields:
            context['only'] = self.only_fields

        return context


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
            if obj.root_services == None:
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
        if 'services' in include_fields:
            context = self.context.copy()
            context['ancestors'] = True
            services_json = ServiceSerializer(obj.services.all(), context=context, many=True).data
            ret['services'] = services_json
        return ret

    class Meta:
        model = Unit
        exclude = ['connection_hash', 'accessibility_property_hash']


def make_muni_ocd_id(name, rest=None):
    s = 'ocd-division/country:%s/%s:%s' % (settings.DEFAULT_COUNTRY, settings.DEFAULT_OCD_MUNICIPALITY, name)
    if rest:
        s += '/' + rest
    return s


class UnitViewSet(munigeo_api.GeoModelAPIView, JSONAPIViewSet, viewsets.ReadOnlyModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer

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
            val = filters['municipality'].lower()
            if val.startswith('ocd-division'):
                ocd_id = val
            else:
                ocd_id = make_muni_ocd_id(val)
            try:
                muni = Municipality.objects.get(division__ocd_id=ocd_id)
            except Municipality.DoesNotExist:
                raise ParseError("municipality with ID '%s' not found" % ocd_id)

            queryset = queryset.filter(municipality=muni)

        if 'provider_type' in filters:
            val = filters.get('provider_type')
            pr_ids = val.split(',')
            queryset = queryset.filter(provider_type__in=pr_ids)

        val = filters.get('service', None)
        if val:
            val = val.lower()
            srv_list = set()
            for srv_id in val.split(','):
                srv_list |= set(Service.objects.all().by_ancestor(srv_id).values_list('id', flat=True))
                srv_list.add(int(srv_id))

            queryset = queryset.filter(services__in=list(srv_list)).distinct()

        val = filters.get('exclude_services', None)
        if val:
            val = val.lower()
            srv_list = set()
            for srv_id in val.split(','):
                srv_list |= set(Service.objects.all().by_ancestor(srv_id).values_list('id', flat=True))
                srv_list.add(int(srv_id))

            queryset = queryset.exclude(services__in=list(srv_list)).distinct()


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
            queryset = queryset.distance(point)

            if 'distance' in filters:
                try:
                    distance = float(filters['distance'])
                    if not distance > 0:
                        raise ValueError()
                except ValueError:
                    raise ParseError("'distance' needs to be a floating point number")
                queryset = queryset.filter(location__distance_lte=(point, distance))
            queryset = queryset.distance(point).order_by('distance')

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

register_view(UnitViewSet, 'unit')

class SearchSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super(SearchSerializer, self).__init__(*args, **kwargs)
        self.serializer_by_model = {}

    def get_result_serializer(self, model, instance):
        ser = self.serializer_by_model.get(model)
        if not ser:
            ser_class = serializers_by_model[model]
            assert model in serializers_by_model, "Serializer for %s not found" % model
            ser = ser_class(context=self.context.copy(), many=False)
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


class SearchViewSet(munigeo_api.GeoModelAPIView, viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = SearchSerializer

    def list(self, request, *args, **kwargs):
        # If the incoming language is not specified, go with the default.
        self.lang_code = request.QUERY_PARAMS.get('language', LANGUAGES[0])
        if self.lang_code not in LANGUAGES:
            raise ParseError("Invalid language supplied. Supported languages: %s" %
                             ','.join(LANGUAGES))

        context = {}
        only = self.request.QUERY_PARAMS.get('only', '')
        if only:
            self.only_fields = [x.strip() for x in only.split(',') if x]
        else:
            self.only_fields = None
        include = self.request.QUERY_PARAMS.get('include', '')
        if only:
            self.include_fields = [x.strip() for x in include.split(',') if x]
        else:
            self.include_fields = None

        input_val = request.QUERY_PARAMS.get('input', '').strip()
        q_val = request.QUERY_PARAMS.get('q', '').strip()
        if not input_val and not q_val:
            raise ParseError("Supply search terms with 'q=' or autocomplete entry with 'input='")
        if input_val and q_val:
            raise ParseError("Supply either 'q' or 'input', not both")

        old_language = translation.get_language()[:2]
        translation.activate(self.lang_code)

        queryset = SearchQuerySet()
        municipality = request.QUERY_PARAMS.get('municipality')
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
            )
        if municipality:
            municipality_queryset = (
                SearchQuerySet()
                .filter(municipality=municipality)
                .filter_or(django_ct='services.service')
            )
            queryset &= municipality_queryset

        Unit.search_objects.fields = self.only_fields
        Unit.search_objects.include_fields = self.include_fields
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
        if ret['service_point_id'] and unit_include:
            params = self.context
            try:
                unit = Unit.objects.get(id=ret['service_point_id'])
            except Unit.DoesNotExist:
                unit = None
            if unit:
                ser = UnitSerializer(unit, context={'only': unit_include.split(',')})
                ret['unit'] = ser.data

        return ret

class AdministrativeDivisionViewSet(munigeo_api.AdministrativeDivisionViewSet):
    serializer_class = AdministrativeDivisionSerializer

register_view(AdministrativeDivisionViewSet, 'administrative_division')
