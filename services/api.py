import json
import re

from django.conf import settings
from django.utils import translation
from django.db.models import Q
from django.contrib.gis.geos import Polygon, MultiPolygon, GeometryCollection
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.gdal import CoordTransform
from modeltranslation.translator import translator, NotRegistered
from rest_framework import serializers, viewsets, generics
from rest_framework.response import Response
from rest_framework.exceptions import ParseError

from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery

from services.models import *
from munigeo.models import *
from munigeo.api import AdministrativeDivisionSerializer, GeoModelSerializer, \
    GeoModelAPIView

# This allows us to find a serializer for Haystack search results
serializers_by_model = {}

all_views = []
def register_view(klass, name, base_name=None):
    entry = {'class': klass, 'name': name}
    if base_name is not None:
        entry['base_name'] = base_name
    all_views.append(entry)

    if klass.serializer_class and hasattr(klass.serializer_class.Meta, 'model'):
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
        model = self.opts.model
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
            del self.fields[field_name]

    def to_native(self, obj):
        ret = super(TranslatedModelSerializer, self).to_native(obj)
        if obj is None:
            return ret

        for field_name in self.translated_fields:
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


class ServiceSerializer(TranslatedModelSerializer, MPTTModelSerializer):
    children = serializers.PrimaryKeyRelatedField(many=True)

    class Meta:
        model = Service

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filter_fields = ['level', 'parent']

    def get_queryset(self):
        queryset = super(ServiceViewSet, self).get_queryset()
        args = self.request.QUERY_PARAMS
        if 'ancestor' in args:
            val = args['ancestor']
            queryset = queryset.by_ancestor(val)
        return queryset

register_view(ServiceViewSet, 'service')


class UnitSerializer(TranslatedModelSerializer, MPTTModelSerializer, GeoModelSerializer):
    class Meta:
        model = Unit


def make_muni_ocd_id(name, rest=None):
    s = 'ocd-division/country:%s/%s:%s' % (settings.DEFAULT_COUNTRY, settings.DEFAULT_OCD_MUNICIPALITY, name)
    if rest:
        s += '/' + rest
    return s


class UnitViewSet(GeoModelAPIView, viewsets.ReadOnlyModelViewSet):
    queryset = Unit.objects.select_related('organization').prefetch_related('services')
    serializer_class = UnitSerializer
    filter_fields = ['services']

    def get_serializer_context(self):
        ret = super(UnitViewSet, self).get_serializer_context()
        ret['srs'] = self.srs
        return ret

    def get_queryset(self):
        queryset = super(UnitViewSet, self).get_queryset()
        filters = self.request.QUERY_PARAMS
        if 'municipality' in filters:
            val = filters['municipality'].lower()
            if val.startswith('ocd-division'):
                ocd_id = val
            else:
                ocd_id = make_muni_ocd_id(val)
            try:
                muni = Municipality.objects.get(ocd_id=ocd_id)
            except Municipality.DoesNotExist:
                raise InvalidFilterError("municipality with ID '%s' not found" % ocd_id)

            queryset = queryset.filter(location__within=muni.geometry.boundary)

        val = filters.get('service', '').lower()
        if val:
            query = Q()
            for srv_id in val.split(','):
                srv_list = Service.objects.all().by_ancestor(srv_id)
                query |= Q(services__in=srv_list)
                query |= Q(services=srv_id)
            queryset = queryset.filter(query).distinct()

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
                    match_re = r'(%s)/([\w_]+):(%s)' % (ocd_id_base, ocd_id_base)
                    m = re.match(match_re, division_path, re.U)
                    if not m:
                        raise InvalidFilterError("'division' must be of form 'muni/type:id'")

                    arr = division_path.split('/')
                    muni_ocd_id = make_muni_ocd_id(arr.pop(0), '/'.join(arr))
                try:
                    div = AdministrativeDivision.objects.select_related('geometry').get(ocd_id=muni_ocd_id)
                except AdministrativeDivision.DoesNotExist:
                    raise InvalidFilterError("administrative division with OCD ID '%s' not found" % muni_ocd_id)
                div_list.append(div)

            div_geom = [div.geometry.boundary for div in div_list]
            if div_list:
                mp = div_list.pop(0).geometry.boundary
                for div in div_list:
                    mp += div.geometry.boundary

            queryset = queryset.filter(location__within=mp)

        return queryset

register_view(UnitViewSet, 'unit')

class SearchSerializer(serializers.Serializer):
    def to_native(self, search_result):
        model = search_result.model
        assert model in serializers_by_model, "Serializer for %s not found" % model
        ser_class = serializers_by_model[model]
        data = ser_class(search_result.object, context=self.context).data
        data['object_type'] = model._meta.model_name
        data['score'] = search_result.score
        return data


class SearchViewSet(GeoModelAPIView, viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = SearchSerializer

    def list(self, request, *args, **kwargs):
        # If the incoming language is not specified, go with the default.
        self.lang_code = request.QUERY_PARAMS.get('language', LANGUAGES[0])
        if self.lang_code not in LANGUAGES:
            raise ParseError("Invalid language supplied. Supported languages: %s" %
                             ','.join(LANGUAGES))

        input_val = request.QUERY_PARAMS.get('input', '').strip()
        q_val = request.QUERY_PARAMS.get('q', '').strip()
        if not input_val and not q_val:
            raise ParseError("Supply search terms with 'q=' or autocomplete entry with 'input='")
        if input_val and q_val:
            raise ParseError("Supply either 'q' or 'input', not both")

        old_language = translation.get_language()[:2]
        translation.activate(self.lang_code)

        queryset = SearchQuerySet()
        if input_val:
            queryset = queryset.filter(autosuggest=input_val)
        else:
            queryset = queryset.filter(text=AutoQuery(q_val))

        self.object_list = queryset.load_all()

        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)

        resp = Response(serializer.data)

        translation.activate(old_language)

        return resp

    """
    def list(self, request):
        resp = []
        context = self.get_serializer_context()

        filter_name = "name_%s__icontains" % lang_code
        obj_hits = Service.objects.filter(**{filter_name: val})
        klass = ServiceSerializer
        for obj in obj_hits[0:5]:
            ser_obj = klass(obj, context=context).data
            ser_obj['object_type'] = 'service'
            resp.append(ser_obj)

        filter_name = "name_%s__icontains" % lang_code
        obj_hits = Unit.objects.filter(**{filter_name: val})
        klass = UnitSerializer
        for obj in obj_hits[0:5]:
            ser_obj = klass(obj, context=context).data
            ser_obj['object_type'] = 'unit'
            resp.append(ser_obj)

        filter_name = "name_%s__icontains" % lang_code
        ad_types = ['neighborhood', 'district', 'sub-district']
        obj_hits = AdministrativeDivision.objects.filter(type__type__in=ad_types).\
            filter(**{filter_name: val})
        klass = AdministrativeDivisionSerializer
        for obj in obj_hits[0:5]:
            ser_obj = klass(obj, context=context).data
            ser_obj['object_type'] = 'administrative_division'
            resp.append(ser_obj)

        return Response(resp)
    """

register_view(SearchViewSet, 'search', base_name='search')
