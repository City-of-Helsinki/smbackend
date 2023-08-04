import logging
import re
import uuid

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.exceptions import ValidationError
from django.db.models import F, Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.utils.module_loading import import_string
from django_filters.rest_framework import DjangoFilterBackend
from modeltranslation.translator import NotRegistered, translator
from mptt.utils import drilldown_tree_for_node
from munigeo import api as munigeo_api
from munigeo.models import AdministrativeDivision, Municipality
from rest_framework import generics, renderers, serializers, viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from observations.models import Observation
from services.accessibility import RULES
from services.models import (
    Announcement,
    Department,
    ErrorMessage,
    Service,
    ServiceNode,
    Unit,
    UnitAccessibilityProperty,
    UnitAccessibilityShortcomings,
    UnitAlias,
    UnitConnection,
    UnitEntrance,
    UnitIdentifier,
    UnitServiceDetails,
)
from services.models.unit import CONTRACT_TYPES, ORGANIZER_TYPES, PROVIDER_TYPES
from services.utils import check_valid_concrete_field

if settings.REST_FRAMEWORK and settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]:
    DEFAULT_RENDERERS = [
        import_string(renderer_module)
        for renderer_module in settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]
    ]
else:
    DEFAULT_RENDERERS = ()


all_views = []


def register_view(klass, name, basename=None):
    entry = {"class": klass, "name": name}
    if basename is not None:
        entry["basename"] = basename
    all_views.append(entry)


LANGUAGES = [x[0] for x in settings.LANGUAGES]

logger = logging.getLogger(__name__)


class MPTTModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(MPTTModelSerializer, self).__init__(*args, **kwargs)
        for field_name in "lft", "rght", "tree_id":
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
                raise ValidationError(
                    {
                        field_name: "This field is a translated field. Instead of a string,"
                        " you must supply an object with strings corresponding"
                        " to desired language ids."
                    }
                )
            for language in (lang[0] for lang in settings.LANGUAGES if lang[0] in obj):
                value = obj[language]  # "musiikkiklubit"
                if language == settings.LANGUAGES[0][0]:  # default language
                    extra_fields[field_name] = value  # { "name": "musiikkiklubit" }
                extra_fields[
                    "{}_{}".format(field_name, language)
                ] = value  # { "name_fi": "musiikkiklubit" }
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
        ret["keywords"] = kw_dict

    def to_representation(self, obj):
        ret = super(TranslatedModelSerializer, self).to_representation(obj)
        if obj is None:
            return ret

        if "keywords" in ret:
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
    return map(
        lambda x: x.id, Service.objects.filter(level=0).filter(tree_id__in=tree_ids)
    )


def root_service_nodes(services):
    # check this
    tree_ids = set(s.tree_id for s in services)
    return map(
        lambda x: x.id, ServiceNode.objects.filter(level=0).filter(tree_id__in=tree_ids)
    )


class JSONAPISerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(JSONAPISerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context", {})
        if "only" in context:
            self.keep_fields = set(context["only"] + ["id"])
            for field_name in list(self.fields.keys()):
                if field_name in self.keep_fields:
                    continue
                del self.fields[field_name]

    def to_representation(self, obj):
        ret = super(JSONAPISerializer, self).to_representation(obj)
        include_fields = self.context.get("include", [])
        if "municipality" in include_fields and obj.municipality:
            muni_json = munigeo_api.MunicipalitySerializer(
                obj.municipality, context=self.context
            ).data
            ret["municipality"] = muni_json
        return ret


class DepartmentSerializer(
    TranslatedModelSerializer, MPTTModelSerializer, JSONAPISerializer
):
    id = serializers.SerializerMethodField("get_uuid")
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Department
        exclude = [
            "uuid",
        ]

    def get_uuid(self, obj):
        return obj.uuid

    def get_parent(self, obj):
        parent = getattr(obj, "parent")
        if parent is not None:
            return parent.uuid
        return None


class ServiceNodeSerializer(
    TranslatedModelSerializer, MPTTModelSerializer, JSONAPISerializer
):
    children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super(ServiceNodeSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        ret = super(ServiceNodeSerializer, self).to_representation(obj)
        include_fields = self.context.get("include", [])
        if "ancestors" in include_fields:
            ancestors = obj.get_ancestors(ascending=True)
            ser = ServiceNodeSerializer(
                ancestors, many=True, context={"only": ["name"]}
            )
            ret["ancestors"] = ser.data
        if "related_services" in include_fields:
            services = obj.related_services
            ser = ServiceSerializer(services, many=True, context={})
            ret["related_services"] = ser.data

        only_fields = self.context.get("only", [])
        if "parent" in only_fields:
            ret["parent"] = obj.parent_id
        ret["period_enabled"] = obj.period_enabled()
        ret["root"] = self.root_service_nodes(obj)
        ret["unit_count"] = dict(
            municipality=dict(
                (
                    (x.division.name_fi.lower() if x.division else "_unknown", x.count)
                    for x in obj.unit_counts.all()
                )
            )
        )
        total = 0
        for _, part in ret["unit_count"]["municipality"].items():
            total += part
        ret["unit_count"]["total"] = total
        return ret

    def root_service_nodes(self, obj):
        return next(root_service_nodes([obj]))

    class Meta:
        model = ServiceNode
        fields = "__all__"


class ServiceSerializer(TranslatedModelSerializer, JSONAPISerializer):
    def to_representation(self, obj):
        ret = super(ServiceSerializer, self).to_representation(obj)
        ret["unit_count"] = {"municipality": {}}
        total = 0
        for unit_count in obj.unit_counts.filter(division_type__type="muni"):
            div_name = unit_count.division.name.lower() if unit_count.division else None
            if unit_count.count == 0:
                continue
            total += unit_count.count
            ret["unit_count"]["municipality"][div_name] = unit_count.count
        ret["unit_count"]["total"] = total
        return ret

    class Meta:
        model = Service
        fields = [
            "name",
            "id",
            "period_enabled",
            "clarification_enabled",
            "keywords",
            "root_service_node",
        ]


class RelatedServiceSerializer(TranslatedModelSerializer, JSONAPISerializer):
    class Meta:
        model = Service
        fields = ["name", "root_service_node"]


class ServiceDetailsSerializer(TranslatedModelSerializer, JSONAPISerializer):
    def to_representation(self, obj):
        ret = super(ServiceDetailsSerializer, self).to_representation(obj)
        service_data = RelatedServiceSerializer(obj.service).data
        ret["name"] = service_data.get("name")
        ret["root_service_node"] = service_data.get("root_service_node")
        if ret["period_begin_year"] is not None:
            ret["period"] = [ret["period_begin_year"], ret.get("period_end_year")]
        else:
            ret["period"] = None
        del ret["period_begin_year"]
        del ret["period_end_year"]
        ret["id"] = obj.service.id
        return ret

    class Meta:
        model = UnitServiceDetails
        fields = ["clarification", "period_begin_year", "period_end_year"]


class JSONAPIViewSetMixin:
    def initial(self, request, *args, **kwargs):
        ret = super(JSONAPIViewSetMixin, self).initial(request, *args, **kwargs)

        include = self.request.query_params.get("include", "")
        self.include_fields = [x.strip() for x in include.split(",") if x]

        self.only_fields = None
        only = self.request.query_params.get("only", "")
        include_geometry = self.request.query_params.get("geometry", "").lower() in (
            "true",
            "1",
        )
        if only:
            self.only_fields = [x.strip() for x in only.split(",") if x]
            if include_geometry:
                self.only_fields.append("geometry")
        return ret

    def get_queryset(self):
        queryset = super(JSONAPIViewSetMixin, self).get_queryset()
        if not self.only_fields:
            return queryset
        model = queryset.model
        # department.uuid is a special case, hardcoded here for now
        fields = [
            f
            for f in self.only_fields + ["uuid"]
            if check_valid_concrete_field(model, f)
        ]
        return queryset.only(*fields)

    def get_serializer_context(self):
        context = super(JSONAPIViewSetMixin, self).get_serializer_context()

        context["include"] = self.include_fields
        if self.only_fields:
            context["only"] = self.only_fields

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

        include_hierarchy = request.query_params.get("include_hierarchy")
        data = serializer.data
        if include_hierarchy is not None and include_hierarchy.lower() not in [
            "no",
            "false",
            "0",
        ]:
            hierarchy = drilldown_tree_for_node(dept)
            data["hierarchy"] = self.serializer_class(
                hierarchy, many=True, context=self.get_serializer_context()
            ).data

        return Response(data)


register_view(DepartmentViewSet, "department")


def choicefield_string(choices, key, obj):
    try:
        return next(x[1] for x in choices if getattr(obj, key) == x[0])
    except StopIteration:
        return None


class UnitConnectionSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    section_type = serializers.SerializerMethodField()

    class Meta:
        model = UnitConnection
        exclude = ["order"]

    def get_section_type(self, obj):
        return choicefield_string(UnitConnection.SECTION_TYPES, "section_type", obj)


class UnitConnectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitConnection.objects.all()
    serializer_class = UnitConnectionSerializer


register_view(UnitConnectionViewSet, "unit_connection")


class UnitEntranceSerializer(TranslatedModelSerializer, munigeo_api.GeoModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = UnitEntrance
        fields = "__all__"

    def get_location(self, obj):
        return munigeo_api.geom_to_json(obj.location, self.srs)


class UnitEntranceViewSet(munigeo_api.GeoModelAPIView, viewsets.ReadOnlyModelViewSet):
    queryset = UnitEntrance.objects.all()
    serializer_class = UnitEntranceSerializer

    def get_serializer_context(self):
        ret = super(UnitEntranceViewSet, self).get_serializer_context()
        ret["srs"] = self.srs
        return ret


register_view(UnitEntranceViewSet, "unit_entrance")


class UnitAccessibilityPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitAccessibilityProperty
        fields = "__all__"


class UnitAccessibilityPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitAccessibilityProperty.objects.all()
    serializer_class = UnitAccessibilityPropertySerializer


class UnitIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitIdentifier
        exclude = ["unit", "id"]


class ServiceNodeViewSet(JSONAPIViewSet, viewsets.ReadOnlyModelViewSet):
    queryset = ServiceNode.objects.all()
    serializer_class = ServiceNodeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ["level", "parent"]

    def get_queryset(self):
        queryset = (
            super(ServiceNodeViewSet, self)
            .get_queryset()
            .prefetch_related(
                "keywords", "related_services", "unit_counts", "unit_counts__division"
            )
        )
        args = self.request.query_params
        if "id" in args:
            id_list = args["id"].split(",")
            queryset = queryset.filter(id__in=id_list)
        if "ancestor" in args:
            val = args["ancestor"]
            queryset = queryset.by_ancestor(val)
        return queryset


register_view(ServiceNodeViewSet, "service_node")


class ServiceViewSet(JSONAPIViewSet, viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_queryset(self):
        queryset = (
            super(ServiceViewSet, self)
            .get_queryset()
            .prefetch_related("keywords", "unit_counts", "unit_counts__division")
        )
        args = self.request.query_params
        if "id" in args:
            id_list = args["id"].split(",")
            queryset = queryset.filter(id__in=id_list)
        return queryset


register_view(ServiceViewSet, "service")


class UnitSerializer(
    TranslatedModelSerializer, munigeo_api.GeoModelSerializer, JSONAPISerializer
):
    connections = UnitConnectionSerializer(many=True)
    entrances = UnitEntranceSerializer(many=True)
    accessibility_properties = UnitAccessibilityPropertySerializer(many=True)
    identifiers = UnitIdentifierSerializer(many=True)
    department = serializers.SerializerMethodField("department_uuid")
    root_department = serializers.SerializerMethodField("root_department_uuid")
    provider_type = serializers.SerializerMethodField()
    organizer_type = serializers.SerializerMethodField()
    contract_type = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(UnitSerializer, self).__init__(*args, **kwargs)
        for f in ("connections", "accessibility_properties", "entrances"):
            if f not in self.fields:
                continue
            ser = self.fields[f]
            if "id" in ser.child.fields:
                del ser.child.fields["id"]
            if "unit" in ser.child.fields:
                del ser.child.fields["unit"]

        self._root_node_cache = {}

    def handle_extension_translations(self, extensions):
        if extensions is None or len(extensions) == 0:
            return extensions
        result = {}
        for key, value in extensions.items():
            translations = {}
            if value is None or value == "None":
                result[key] = None
                continue
            for lang in LANGUAGES:
                with translation.override(lang):
                    translated_value = translation.gettext(value)
                    if translated_value != value:
                        translations[lang] = translated_value
                    translated_value = None
            if len(translations) > 0:
                result[key] = translations
            else:
                result[key] = value
        return result

    def _department_uuid(self, obj, field):
        if getattr(obj, field) is not None:
            return getattr(obj, field).uuid
        return None

    def department_uuid(self, obj):
        return self._department_uuid(obj, "department")

    def root_department_uuid(self, obj):
        return self._department_uuid(obj, "root_department")

    def get_provider_type(self, obj):
        return choicefield_string(PROVIDER_TYPES, "provider_type", obj)

    def get_organizer_type(self, obj):
        return choicefield_string(ORGANIZER_TYPES, "organizer_type", obj)

    def get_contract_type(self, obj):
        key = choicefield_string(CONTRACT_TYPES, "contract_type", obj)
        if not key:
            return None
        translations = {}
        for lang in LANGUAGES:
            with translation.override(lang):
                translations[lang] = translation.gettext(key)
        return {"id": key, "description": translations}

    def to_representation(self, obj):
        ret = super(UnitSerializer, self).to_representation(obj)
        if hasattr(obj, "distance") and obj.distance:
            ret["distance"] = obj.distance.m

        if "root_service_nodes" in ret:
            if obj.root_service_nodes is None or obj.root_service_nodes == "":
                ret["root_service_nodes"] = None
            else:
                ret["root_service_nodes"] = [
                    int(x) for x in obj.root_service_nodes.split(",")
                ]

        include_fields = self.context.get("include", [])
        for field in ["department", "root_department"]:
            if field in include_fields:
                dep_json = DepartmentSerializer(
                    getattr(obj, field), context=self.context
                ).data
                ret[field] = dep_json
        # Not using actual serializer instances below is a performance optimization.
        if "service_nodes" in include_fields:
            service_nodes_json = []
            for s in obj.service_nodes.all():
                # Optimization:
                # Store root nodes by tree_id in a dict because otherwise
                # this would generate multiple db queries for every single unit
                tree_id = s._mpttfield("tree_id")  # Forget your privacy!
                root_node = self._root_node_cache.get(tree_id)
                if root_node is None:
                    root_node = s.get_root()
                    self._root_node_cache[tree_id] = root_node

                name = {}
                for lang in LANGUAGES:
                    name[lang] = getattr(s, "name_{0}".format(lang))
                data = {
                    "id": s.id,
                    "name": name,
                    "root": root_node.id,
                    "service_reference": s.service_reference,
                }
                # if s.identical_to:
                #    data['identical_to'] = getattr(s.identical_to, 'id', None)
                if s.level is not None:
                    data["level"] = s.level
                service_nodes_json.append(data)
            ret["service_nodes"] = service_nodes_json
        if "services" in include_fields:
            ret["services"] = ServiceDetailsSerializer(
                obj.service_details, many=True
            ).data
        if "accessibility_properties" in include_fields:
            acc_props = [
                {"variable": s.variable_id, "value": s.value}
                for s in obj.accessibility_properties.all()
            ]
            ret["accessibility_properties"] = acc_props

        if "connections" in include_fields:
            ret["connections"] = UnitConnectionSerializer(
                obj.connections, many=True
            ).data

        if "extensions" in ret:
            ret["extensions"] = self.handle_extension_translations(ret["extensions"])

        try:
            shortcomings = obj.accessibility_shortcomings
        except UnitAccessibilityShortcomings.DoesNotExist:
            shortcomings = UnitAccessibilityShortcomings()
        if "accessibility_shortcoming_count" in getattr(
            self, "keep_fields", ["accessibility_shortcoming_count"]
        ):
            ret[
                "accessibility_shortcoming_count"
            ] = shortcomings.accessibility_shortcoming_count

        if "request" not in self.context:
            return ret
        qparams = self.context["request"].query_params
        if qparams.get("geometry", "").lower() in ("true", "1"):
            geom = obj.geometry  # TODO: different geom types
            if geom and obj.geometry != obj.location:
                ret["geometry"] = munigeo_api.geom_to_json(geom, self.srs)
        elif "geometry" in ret:
            del ret["geometry"]

        if qparams.get("accessibility_description", "").lower() in ("true", "1"):
            ret["accessibility_description"] = shortcomings.accessibility_description
        return ret

    class Meta:
        model = Unit
        exclude = [
            "connection_hash",
            "service_details_hash",
            "accessibility_property_hash",
            "identifier_hash",
            "public",
            "search_column_fi",
            "search_column_sv",
            "search_column_en",
        ]


def make_muni_ocd_id(name, rest=None):
    s = "ocd-division/country:%s/%s:%s" % (
        settings.DEFAULT_COUNTRY,
        settings.DEFAULT_OCD_MUNICIPALITY,
        name,
    )
    if rest:
        s += "/" + rest
    return s


def get_fields(place, lang_code, fields):
    for field in fields:
        p = place[field]
        if p and lang_code in p:
            place[field] = p[lang_code]
        else:
            place[field] = ""
    return place


class KmlRenderer(renderers.BaseRenderer):
    media_type = "application/vnd.google-earth.kml+xml"
    format = "kml"

    def render(self, data, media_type=None, renderer_context=None):
        resp = {}
        lang_code = renderer_context["view"].request.query_params.get(
            "language", LANGUAGES[0]
        )
        if lang_code not in LANGUAGES:
            raise ParseError(
                "Invalid language supplied. Supported languages: %s"
                % ",".join(LANGUAGES)
            )
        resp["lang_code"] = lang_code
        places = data.get("results", [data])
        resp["places"] = [
            get_fields(place, lang_code, settings.KML_TRANSLATABLE_FIELDS)
            for place in places
        ]
        return render_to_string("kml.xml", resp)


class UnitViewSet(
    munigeo_api.GeoModelAPIView, JSONAPIViewSet, viewsets.ReadOnlyModelViewSet
):
    queryset = Unit.objects.filter(public=True, is_active=True)
    serializer_class = UnitSerializer
    renderer_classes = DEFAULT_RENDERERS + [KmlRenderer]
    filter_backends = (DjangoFilterBackend,)

    def __init__(self, *args, **kwargs):
        super(UnitViewSet, self).__init__(*args, **kwargs)
        self.service_details = False

    def get_serializer_context(self):
        ret = super(UnitViewSet, self).get_serializer_context()
        ret["srs"] = self.srs
        ret["service_details"] = self._service_details_requested()
        return ret

    def _service_details_requested(self):
        return "services" in self.include_fields

    def get_queryset(self):
        queryset = super(UnitViewSet, self).get_queryset()

        queryset = queryset.prefetch_related("accessibility_shortcomings")
        if self._service_details_requested():
            queryset = queryset.prefetch_related("service_details")
            queryset = queryset.prefetch_related("service_details__service")

        filters = self.request.query_params
        if "id" in filters:
            id_list = filters["id"].split(",")
            queryset = queryset.filter(id__in=id_list)

        if "municipality" in filters:
            val = filters["municipality"].lower().strip()
            if len(val) > 0:
                municipalities = val.split(",")
                muni_sq = Q()

                for municipality_raw in municipalities:
                    municipality = municipality_raw.strip()
                    if municipality.startswith("ocd-division"):
                        ocd_id = municipality
                    else:
                        ocd_id = make_muni_ocd_id(municipality)
                    try:
                        muni = Municipality.objects.get(division__ocd_id=ocd_id)
                        muni_sq |= Q(municipality=muni)
                    except Municipality.DoesNotExist:
                        raise ParseError("municipality with ID '%s' not found" % ocd_id)

                queryset = queryset.filter(muni_sq)

        if "city_as_department" in filters:
            val = filters["city_as_department"].lower().strip()

            if len(val) > 0:
                deps_uuids = val.split(",")

                for deps_uuid in deps_uuids:
                    try:
                        uuid.UUID(deps_uuid)
                    except ValueError:
                        raise serializers.ValidationError(
                            "'city_as_department' value must be a valid UUID"
                        )

                deps = Department.objects.filter(uuid__in=deps_uuids).select_related(
                    "municipality"
                )
                munis = [d.municipality for d in deps]

                queryset = queryset.filter(root_department__in=deps) | queryset.filter(
                    municipality__in=munis
                )

        if "provider_type" in filters:
            val = filters.get("provider_type")
            pr_ids = val.split(",")
            queryset = queryset.filter(provider_type__in=pr_ids)

        if "provider_type__not" in filters:
            val = filters.get("provider_type__not")
            pr_ids = val.split(",")
            queryset = queryset.exclude(provider_type__in=pr_ids)

        level = filters.get("level", None)
        level_specs = None
        if level:
            if level != "all":
                level_specs = settings.LEVELS.get(level)

        def service_nodes_by_ancestors(service_node_ids):
            srv_list = set()
            for srv_id in service_node_ids:
                srv_list |= set(
                    ServiceNode.objects.all()
                    .by_ancestor(srv_id)
                    .values_list("id", flat=True)
                )
                srv_list.add(int(srv_id))
            return list(srv_list)

        service_nodes = filters.get("service_node", None)

        def validate_service_node_ids(service_node_ids):
            return [
                str(service_node_id).strip()
                for service_node_id in service_node_ids
                if service_node_id.isdigit()
            ]

        service_node_ids = None
        if service_nodes:
            service_nodes = service_nodes.lower()
            service_node_ids = validate_service_node_ids(service_nodes.split(","))
        elif level_specs:
            if level_specs["type"] == "include":
                service_node_ids = level_specs["service_nodes"]
        if service_node_ids:
            queryset = queryset.filter(
                service_nodes__in=service_nodes_by_ancestors(service_node_ids)
            ).distinct()

        service_node_ids = None
        val = filters.get("exclude_service_nodes", None)
        if val:
            val = val.lower()
            service_node_ids = validate_service_node_ids(val.split(","))
        elif level_specs:
            if level_specs["type"] == "exclude":
                service_node_ids = level_specs["service_nodes"]
        if service_node_ids:
            queryset = queryset.exclude(
                service_nodes__in=service_nodes_by_ancestors(service_node_ids)
            ).distinct()

        services = filters.get("service")
        if services is not None:
            queryset = queryset.filter(services__in=services.split(",")).distinct()

        if "division" in filters:
            # Divisions can be specified with form:
            # division=helsinki/kaupunginosa:kallio,vantaa/äänestysalue:5
            d_list = filters["division"].lower().split(",")
            div_list = []
            for division_path in d_list:
                if division_path.startswith("ocd-division"):
                    muni_ocd_id = division_path
                else:
                    ocd_id_base = r"[\w0-9~_.-]+"
                    match_re = r"(%s)/([\w_-]+):(%s)" % (ocd_id_base, ocd_id_base)
                    m = re.match(match_re, division_path, re.U)
                    if not m:
                        raise ParseError("'division' must be of form 'muni/type:id'")

                    arr = division_path.split("/")
                    muni_ocd_id = make_muni_ocd_id(arr.pop(0), "/".join(arr))
                try:
                    div = AdministrativeDivision.objects.select_related("geometry").get(
                        ocd_id=muni_ocd_id
                    )
                except AdministrativeDivision.DoesNotExist:
                    raise ParseError(
                        "administrative division with OCD ID '%s' not found"
                        % muni_ocd_id
                    )
                div_list.append(div)

            if div_list:
                mp = div_list.pop(0).geometry.boundary
                for div in div_list:
                    mp += div.geometry.boundary

            queryset = queryset.filter(location__within=mp)

        if "lat" in filters and "lon" in filters:
            try:
                lat = float(filters["lat"])
                lon = float(filters["lon"])
            except ValueError:
                raise ParseError("'lat' and 'lon' need to be floating point numbers")
            point = Point(lon, lat, srid=4326)

            if "distance" in filters:
                try:
                    distance = float(filters["distance"])
                    if not distance > 0:
                        raise ValueError()
                except ValueError:
                    raise ParseError("'distance' needs to be a floating point number")
                queryset = queryset.filter(
                    location__distance_lte=(point, D(m=distance))
                )
            queryset = queryset.annotate(distance=Distance("location", point)).order_by(
                "distance"
            )

        if "bbox" in filters:
            val = self.request.query_params.get("bbox", None)
            if "bbox_srid" in filters:
                ref = SpatialReference(filters.get("bbox_srid", None))
            else:
                ref = self.srs
            if val:
                bbox_filter = munigeo_api.build_bbox_filter(ref, val, "location")
                bbox_geometry_filter = munigeo_api.build_bbox_filter(
                    ref, val, "geometry"
                )
                queryset = queryset.filter(Q(**bbox_filter) | Q(**bbox_geometry_filter))

        if "category" in filters:
            services_and_service_nodes = filters.get("category", None).split(",")
            service_ids = []
            servicenode_ids = []
            for category in services_and_service_nodes:
                key = category.split(":")[0]
                value = category.split(":")[1]
                if key == "service":
                    service_ids.append(value)
                elif key == "service_node":
                    servicenode_ids.append(value)
            queryset = queryset.filter(
                Q(services__in=service_ids)
                | Q(service_nodes__in=service_nodes_by_ancestors(servicenode_ids))
            ).distinct()

        if "address" in filters:
            language = filters["language"] if "language" in filters else "fi"
            address_splitted = filters["address"].split(" ")
            key = f"street_address_{language}"
            if len(address_splitted) == 1:
                key += "__startswith"
                arg = address_splitted[0]

            else:
                key += "__iregex"
                arg = filters["address"] + r"($|\s|,|[a-zA-Z]).*"
            queryset = queryset.filter(**{key: arg})

        maintenance_organization = self.request.query_params.get(
            "maintenance_organization"
        )
        if maintenance_organization:
            queryset = queryset.filter(
                Q(extensions__maintenance_organization=maintenance_organization)
                | Q(
                    extensions__additional_maintenance_organization=maintenance_organization
                )
            )

        if "observations" in self.include_fields:
            queryset = (
                queryset.prefetch_related(
                    Prefetch(
                        "observation_set",
                        queryset=Observation.objects.filter(
                            Q(property__expiration=None)
                            | Q(time__gt=timezone.now() - F("property__expiration"))
                        ),
                    )
                )
                .prefetch_related("observation_set__property__allowed_values")
                .prefetch_related("observation_set__value")
            )

        if "service_nodes" in self.include_fields:
            queryset = queryset.prefetch_related("service_nodes")

        for field in ["connections", "accessibility_properties", "keywords"]:
            if self._should_prefetch_field(field):
                queryset = queryset.prefetch_related(field)

        return queryset

    def _should_prefetch_field(self, field_name):
        # These fields are included by default,
        # and only omitted if not part of an 'only' query param
        return (
            self.only_fields is None
            or len(self.only_fields) == 0
            or field_name in self.only_fields
            or field_name in self.include_fields
        )

    def _add_content_disposition_header(self, response):
        if isinstance(response.accepted_renderer, KmlRenderer):
            header = "attachment; filename={}".format("palvelukartta.kml")
            response["Content-Disposition"] = header
        return response

    def retrieve(self, request, pk=None):
        try:
            int(pk)
        except ValueError:
            raise Http404

        try:
            unit = Unit.objects.get(pk=pk, public=True, is_active=True)
        except Unit.DoesNotExist:
            unit_alias = get_object_or_404(UnitAlias, second=pk)
            unit = unit_alias.first
        serializer = self.serializer_class(unit, context=self.get_serializer_context())
        return Response(serializer.data)

    def list(self, request, **kwargs):
        response = super(UnitViewSet, self).list(request)
        response.add_post_render_callback(self._add_content_disposition_header)
        return response


register_view(UnitViewSet, "unit")


class AccessibilityRuleView(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = None

    def list(self, request, *args, **kwargs):
        rules, messages = RULES.get_data()
        return Response({"rules": rules, "messages": messages})


register_view(
    AccessibilityRuleView, "accessibility_rule", basename="accessibility_rule"
)


class AdministrativeDivisionSerializer(munigeo_api.AdministrativeDivisionSerializer):
    def to_representation(self, obj):
        ret = super(AdministrativeDivisionSerializer, self).to_representation(obj)
        if "request" not in self.context:
            return ret

        query_params = self.context["request"].query_params
        unit_include = query_params.get("unit_include", None)
        service_point_id = ret["service_point_id"]

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
                ser = UnitSerializer(unit, context={"only": unit_include.split(",")})
                ret["unit"] = ser.data

        unit_ids = ret["units"]
        if unit_ids and unit_include:
            units = Unit.objects.filter(id__in=unit_ids)
            if units:
                units_data = []
                for unit in units:
                    units_data.append(
                        UnitSerializer(
                            unit, context={"only": unit_include.split(",")}
                        ).data
                    )
                ret["units"] = units_data

        include_fields = query_params.get("include", [])
        if "centroid" in include_fields and obj.geometry:
            centroid = obj.geometry.boundary.centroid
            ret["centroid"] = munigeo_api.geom_to_json(centroid, self.srs)

        return ret


class AdministrativeDivisionViewSet(munigeo_api.AdministrativeDivisionViewSet):
    serializer_class = AdministrativeDivisionSerializer


register_view(AdministrativeDivisionViewSet, "administrative_division")


class AddressViewSet(munigeo_api.AddressViewSet):
    serializer_class = munigeo_api.AddressSerializer


register_view(AddressViewSet, "address")


class PostalCodeAreaViewSet(munigeo_api.PostalCodeAreaViewSet):
    serializers_class = munigeo_api.PostalCodeSerializer


register_view(PostalCodeAreaViewSet, "postalcodearea")


class AnnouncementSerializer(TranslatedModelSerializer, JSONAPISerializer):
    class Meta:
        model = Announcement
        exclude = ["id", "active"]


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Announcement.objects.filter(active=True)
    serializer_class = AnnouncementSerializer


register_view(AnnouncementViewSet, "announcement")


class ErrorMessageSerializer(TranslatedModelSerializer, JSONAPISerializer):
    class Meta:
        model = ErrorMessage
        exclude = ["id", "active"]


class ErrorMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ErrorMessage.objects.filter(active=True)
    serializer_class = ErrorMessageSerializer


register_view(ErrorMessageViewSet, "error_message")
