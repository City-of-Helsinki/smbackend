import json

from django.conf import settings
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.exceptions import InvalidFilterError, BadRequest
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.cache import SimpleCache

from services.models import *

LANGUAGES = [x[0] for x in settings.LANGUAGES]

class TranslatableCachedResource(ModelResource):
    def __init__(self, api_name=None):
        super(TranslatableCachedResource, self).__init__(api_name)
        self._meta.cache = SimpleCache(timeout=3600)

    def dehydrate(self, bundle):
        bundle = super(TranslatableCachedResource, self).dehydrate(bundle)
        obj = bundle.obj
        for f_name in obj._meta.translatable_fields:
            if f_name in bundle.data:
                del bundle.data[f_name]
            for lang in LANGUAGES:
                key = "%s_%s" % (f_name, lang)
                if key in bundle.data:
                    del bundle.data[key]

            d = {}
            default_lang = LANGUAGES[0]
            d[default_lang] = getattr(obj, f_name)
            for lang in LANGUAGES[1:]:
                key = "%s_%s" % (f_name, lang)
                d[lang] = getattr(bundle.obj, key)
            bundle.data[f_name] = d

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

class UnitResource(TranslatableCachedResource):
    organization = fields.ForeignKey(OrganizationResource, 'organization')
    department = fields.ForeignKey(DepartmentResource, 'department', null=True)

    def dehydrate(self, bundle):
        bundle = super(UnitResource, self).dehydrate(bundle)
        obj = bundle.obj
        location_str = bundle.obj.location.geojson
        bundle.data['location'] = json.loads(location_str)
        return bundle

    class Meta:
        queryset = Unit.objects.all()
        excludes = ['location']

all_resources = [DepartmentResource, OrganizationResource, ServiceResource, UnitResource]
