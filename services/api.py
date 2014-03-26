import json
import re

from django.conf import settings
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.exceptions import InvalidFilterError, ApiFieldError, BadRequest, NotFound
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from django.contrib.gis.geos import Polygon, MultiPolygon, GeometryCollection
from django.contrib.gis.gdal import CoordTransform

from services.models import *
from munigeo.models import *
from munigeo.api import build_bbox_filter, srid_to_srs, TranslatableCachedResource


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
            'level': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'parent': ALL_WITH_RELATIONS,
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
