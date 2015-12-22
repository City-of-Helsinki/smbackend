import json
import re

from django.conf import settings
from django.utils import translation
from django.db.models import Q
from django.contrib.gis.geos import Polygon, MultiPolygon, GeometryCollection, Point
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from modeltranslation.translator import translator, NotRegistered
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.views import APIView

from haystack.query import SearchQuerySet, ValuesListSearchQuerySet
from haystack.inputs import AutoQuery

from services.models import *
from services.accessibility import RULES as accessibility_rules
from services.serializers import *
from munigeo.models import *
from munigeo import api as munigeo_api

LANGUAGES = [x[0] for x in settings.LANGUAGES]

class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

register_view(OrganizationViewSet, 'organization')

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

register_view(DepartmentViewSet, 'department')

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

class UnitConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitConnection.objects.all()
    serializer_class = UnitConnectionSerializer

register_view(UnitConnectionViewSet, 'unit_connection')

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
        return queryset.values_list('id', flat=True)

register_view(ServiceViewSet, 'service')

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

        return queryset.values_list('id', flat=True)

register_view(UnitViewSet, 'unit')


class SearchViewSet(munigeo_api.GeoModelAPIView, viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = SearchSerializer

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
                .filter_or(address=q_val)
            )
        if municipality:
            municipality_queryset = (
                SearchQuerySet()
                .filter(municipality=municipality)
                .filter_or(django_ct='services.service')
                .filter_or(django_ct='munigeo.address')
            )
            queryset &= municipality_queryset

        only = getattr(self, 'only_fields') or {}
        include = getattr(self, 'include_fields') or {}
        Unit.search_objects.only_fields = only.get('unit')
        Unit.search_objects.include_fields = include.get('unit')

        self.object_list = queryset.values_list('id', 'score', flat=False)

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


class AdministrativeDivisionViewSet(munigeo_api.AdministrativeDivisionViewSet):
    serializer_class = AdministrativeDivisionSerializer

register_view(AdministrativeDivisionViewSet, 'administrative_division')

class AddressViewSet(munigeo_api.AddressViewSet):
    serializer_class = munigeo_api.AddressSerializer

register_view(AddressViewSet, 'address')
