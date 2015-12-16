from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers
from services.models import *
from munigeo.models import *
from munigeo import api as munigeo_api
from modeltranslation.translator import translator, NotRegistered
import hashlib

LANGUAGES = [x[0] for x in settings.LANGUAGES]

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

class DepartmentSerializer(TranslatedModelSerializer):
    class Meta:
        model = Department

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

def root_services(services):
    tree_ids = set(s.tree_id for s in services)
    return map(lambda x: x.id,
               Service.objects.filter(level=0).filter(
                   tree_id__in=tree_ids))

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

class UnitConnectionSerializer(TranslatedModelSerializer):
    class Meta:
        model = UnitConnection
class UnitAccessibilityPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitAccessibilityProperty

class UnitIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitIdentifier
        exclude = ['unit', 'id']

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

    def make_cache_key(self, params, obj):
        params = self.context.get('request').QUERY_PARAMS
        representation_key = self._representation_spec_key(params)
        return "sm_unit_{}_{}".format(representation_key, obj.pk)

    def _representation_spec_key(self, params):
        only = sorted(params.get('only', []))
        include = sorted(params.get('include', []))
        srid = params.get('srid') or []
        key_path = only + include + srid
        key_str = '/'.join(key_path).encode('utf-8')
        return hashlib.md5(key_str).hexdigest()

    def to_representation(self, obj):
        cache_key = self.make_cache_key('unit', obj)
        data = cache.get(cache_key)

        if data:
            return data

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
                    services_json.append({'id': s.id, 'name': name})
            ret['services'] = services_json
        if 'accessibility_properties' in include_fields:
            acc_props = [{'variable': s.variable_id, 'value': s.value}
                         for s in obj.accessibility_properties.all()]
            ret['accessibility_properties'] = acc_props

        cache.set(cache_key, ret)
        return ret

    class Meta:
        model = Unit
        exclude = [
            'connection_hash', 'accessibility_property_hash',
            'identifier_hash',
        ]

