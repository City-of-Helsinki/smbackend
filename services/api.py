import json
import re

from django.conf import settings
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.exceptions import InvalidFilterError, ApiFieldError, BadRequest, NotFound
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.cache import SimpleCache
from django.contrib.gis.geos import Polygon, MultiPolygon, GeometryCollection
from django.contrib.gis.gdal import SRSException, SpatialReference, CoordTransform

from services.models import *
from munigeo.models import *

# Use the GPS coordinate system by default
DEFAULT_SRID = 4326

LANGUAGES = [x[0] for x in settings.LANGUAGES]

def poly_from_bbox(bbox_val):
    points = bbox_val.split(',')
    if len(points) != 4:
        raise InvalidFilterError("bbox must be in format 'left,bottom,right,top'")
    try:
        points = [float(p) for p in points]
    except ValueError:
        raise InvalidFilterError("bbox values must be floating point or integers")
    poly = Polygon.from_bbox(points)
    return poly

def srid_to_srs(srid):
    if not srid:
        srid = DEFAULT_SRID
    try:
        srid = int(srid)
    except ValueError:
        raise InvalidFilterError("'srid' must be an integer")
    try:
        srs = SpatialReference(srid)
    except SRSException:
        raise InvalidFilterError("SRID %d not found (try 4326 for GPS coordinate system)" % srid)
    return srs

def build_bbox_filter(srid, bbox_val, field_name):
    poly = poly_from_bbox(bbox_val)
    srs = srid_to_srs(srid)
    poly.set_srid(srs.srid)

    if srid != settings.PROJECTION_SRID:
        source_srs = SpatialReference(settings.PROJECTION_SRID)
        ct = CoordTransform(srs, source_srs)
        poly.transform(ct)

    return {"%s__within" % field_name: poly}

class TranslatableCachedResource(ModelResource):
    def __init__(self, api_name=None):
        super(TranslatableCachedResource, self).__init__(api_name)
        self._meta.cache = SimpleCache(timeout=3600)

    def dehydrate(self, bundle):
        bundle = super(TranslatableCachedResource, self).dehydrate(bundle)
        obj = bundle.obj
        for field_name in obj._meta.translatable_fields:
            if field_name in bundle.data:
                del bundle.data[field_name]

            # Remove the pre-existing data in the bundle.
            for lang in LANGUAGES:
                key = "%s_%s" % (field_name, lang)
                if key in bundle.data:
                    del bundle.data[key]

            d = {}
            default_lang = LANGUAGES[0]
            d[default_lang] = getattr(obj, field_name)
            for lang in LANGUAGES[1:]:
                key = "%s_%s" % (field_name, lang)
                d[lang] = getattr(bundle.obj, key)

            # If no text provided, leave the field as null
            for key, val in d.items():
                if val != None:
                    break
            else:
                d = None
            bundle.data[field_name] = d

        return bundle
    #_meta.translatable_fields

class OrganizationResource(TranslatableCachedResource):
    class Meta:
        queryset = Organization.objects.all()

class DepartmentResource(TranslatableCachedResource):
    organization = fields.ForeignKey(OrganizationResource, 'organization')

    class Meta:
        queryset = Department.objects.all()

class ServiceResource(TranslatableCachedResource):
    parent = fields.ForeignKey('services.api.ServiceResource', 'parent', null=True)

    class Meta:
        queryset = Service.objects.all()
        excludes = ['lft', 'rght', 'tree_id']
        filtering = {
            'level': ['exact', 'lt', 'lte', 'gt', 'gte']
        }


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

        if 'district' in filters:
            # Districts can be specified with form:
            # district=helsinki/kaupunginosa:kallio,vantaa/äänestysalue:5
            d_list = filters['district'].lower().split(',')
            div_list = []
            for district_path in d_list:
                ocd_id_base = r'[\w0-9~_.-]+'
                match_re = r'(%s)/([\w_]+):(%s)' % (ocd_id_base, ocd_id_base)
                m = re.match(match_re, district_path, re.U)
                if not m:
                    raise InvalidFilterError("'district' must be of form 'muni/type:id'")

                arr = district_path.split('/')
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
        queryset = Unit.geo_objects.all()
        excludes = ['location']
        filtering = {
            'services': ALL_WITH_RELATIONS
        }

all_resources = [DepartmentResource, OrganizationResource, ServiceResource, UnitResource]
