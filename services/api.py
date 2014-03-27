import json
import re

from django.conf import settings
#from tastypie import fields
#from tastypie.resources import ModelResource
#from tastypie.exceptions import InvalidFilterError, ApiFieldError, BadRequest, NotFound
#from tastypie.constants import ALL, ALL_WITH_RELATIONS
from django.contrib.gis.geos import Polygon, MultiPolygon, GeometryCollection
from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.gdal import CoordTransform
from modeltranslation.translator import translator, NotRegistered
from rest_framework import serializers, viewsets

from services.models import *
from munigeo.models import *

LANGUAGES = [x[0] for x in settings.LANGUAGES]

class MPTTModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(MPTTModelSerializer, self).__init__(*args, **kwargs)
        for field_name in 'lft', 'rght', 'tree_id':
            if field_name in self.fields:
                del self.fields[field_name]

class GeoModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(GeoModelSerializer, self).__init__(*args, **kwargs)
        model = self.opts.model
        self.geo_fields = []
        model_fields = [f.name for f in model._meta.fields]
        for field_name in self.fields:
            if not field_name in model_fields:
                continue
            field = model._meta.get_field(field_name)
            if not isinstance(field, GeometryField):
                continue
            self.geo_fields.append(field_name)
            del self.fields[field_name]

    def to_native(self, obj):
        ret = super(GeoModelSerializer, self).to_native(obj)
        if obj is None:
            return ret
        for field_name in self.geo_fields:
            val = getattr(obj, field_name)
            if val == None:
                ret[field_name] = None
                continue
            s = val.geojson
            ret[field_name] = json.loads(s)
        return ret

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
            default_lang = LANGUAGES[0]
            d[default_lang] = getattr(obj, field_name)
            for lang in LANGUAGES[1:]:
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


class OrganizationSerializer(serializers.HyperlinkedModelSerializer, TranslatedModelSerializer):
    class Meta:
        model = Organization

class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class DepartmentSerializer(serializers.HyperlinkedModelSerializer, TranslatedModelSerializer):
    class Meta:
        model = Department

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class ServiceSerializer(serializers.HyperlinkedModelSerializer, TranslatedModelSerializer, MPTTModelSerializer):
    class Meta:
        model = Service

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filter_fields = ['level', 'parent']


class UnitSerializer(serializers.HyperlinkedModelSerializer, TranslatedModelSerializer, MPTTModelSerializer, GeoModelSerializer):
    class Meta:
        model = Unit

class UnitViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


all_resources = {
    'organization': OrganizationViewSet,
    'department': DepartmentViewSet,
    'service': ServiceViewSet,
    'unit': UnitViewSet,
}

"""
from munigeo.api import build_bbox_filter, srid_to_srs, TranslatableCachedResource

def make_muni_ocd_id(name, rest=None):
    s = 'ocd-division/country:%s/%s:%s' % (settings.DEFAULT_COUNTRY, settings.DEFAULT_OCD_MUNICIPALITY, name)
    if rest:
        s += '/' + rest
    return s


class UnitResource(TranslatableCachedResource):
    organization = fields.ForeignKey(OrganizationResource, 'organization')
    department = fields.ForeignKey(DepartmentResource, 'department', null=True)
    services = fields.ManyToManyField(ServiceResource, 'services', null=True)

    def build_filters(self, filters=None):
        orm_filters = super(UnitResource, self).build_filters(filters)
        if not filters:
            return orm_filters

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

            orm_filters['location__within'] = muni.geometry.boundary
        else:
            muni = None

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
            orm_filters['location__within'] = mp

        if 'bbox' in filters:
            srid = filters.get('srid', None)
            bbox_filter = build_bbox_filter(srid, filters['bbox'], 'location')
            orm_filters.update(bbox_filter)

        return orm_filters

    def dehydrate_location(self, bundle):
        srid = bundle.request.GET.get('srid', None)
        srs = srid_to_srs(srid)
        geom = bundle.obj.location
        if srs.srid != geom.srid:
            ct = CoordTransform(geom.srs, srs)
            geom.transform(ct)
        location_str = geom.geojson
        return json.loads(location_str)

    def dehydrate(self, bundle):
        bundle = super(UnitResource, self).dehydrate(bundle)
        obj = bundle.obj

        if obj.location != None:
            bundle.data['location'] = self.dehydrate_location(bundle)

        return bundle

    class Meta:
        queryset = Unit.geo_objects.all().select_related('organization').prefetch_related('services')
        excludes = ['location']
        filtering = {
            'services': ALL_WITH_RELATIONS,
            'name': ALL
        }

all_resources = [DepartmentResource, OrganizationResource, ServiceResource, UnitResource]
"""
