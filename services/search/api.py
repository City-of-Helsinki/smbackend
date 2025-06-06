"""
Brief explanation how full text search is implemented in the smbackend.
- Currently search is performed to following models, Unit, Service,
munigeo_Address, munigeo_Administrative_division.
- For every model that is included in the search a search column is added
for every language of type SearchVector. These are also defined as a Gindex.
 The models that are searched also implements a function called
  get_search_column_indexing where the name, configuration(language) and weight of the
  columns that will be indexed are defined. This function is used by the indexing script
  and signals when the search_column is populated.
- A view called search_view is created. It contains the search_columns of the models
and a couple auxiliary columns: id. type_name and name. This view is created by a
raw SQL migration 008X_create_search_view.py.
- The search if performed by querying the views search_columns.
- For models included in the search a post_save signal is connected and the
  search_column is updated when they are saved.
- The search_columns can be manually updated with  the index_search_columns
and emptied with the empty_search_columns management script.
"""

import logging
import re
from itertools import chain

from django.contrib.gis.gdal import SpatialReference
from django.db import connection, reset_queries
from django.db.models import Count
from drf_spectacular.utils import OpenApiParameter, extend_schema
from munigeo import api as munigeo_api
from munigeo.models import Address, AdministrativeDivision
from munigeo.utils import get_default_srid
from rest_framework import serializers, status
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from services.api import (
    TranslatedModelSerializer,
    UnitConnectionSerializer,
    UnitSerializer,
)
from services.models import (
    Department,
    ExclusionRule,
    Service,
    ServiceNode,
    Unit,
    UnitAccessibilityShortcomings,
)
from services.utils import strtobool

from .constants import (
    DEFAULT_MODEL_LIMIT_VALUE,
    DEFAULT_RANK_THRESHOLD,
    DEFAULT_SEARCH_SQL_LIMIT_VALUE,
    DEFAULT_SRS,
    DEFAULT_TRIGRAM_THRESHOLD,
    LANGUAGES,
    QUERY_PARAM_TYPE_NAMES,
)
from .utils import (
    get_all_ids_from_sql_results,
    get_preserved_order,
    get_service_node_results,
    get_trigram_results,
    has_exclusion_word_in_query,
    set_address_fields,
    set_service_node_unit_count,
    set_service_unit_count,
)

logger = logging.getLogger("services.search")


class RootServiceNodeSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = ServiceNode
        fields = ["id", "name"]


class DepartmentSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid")

    class Meta:
        model = Department
        fields = ["id", "name", "street_address", "municipality"]


class RootDepartmentSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid")

    class Meta:
        model = Department
        fields = ["id", "name"]


class SearchSerializer(serializers.Serializer):
    def to_representation(self, obj):
        representation = super().to_representation(obj)
        object_type = None
        if isinstance(obj, Unit):
            object_type = "unit"
        elif isinstance(obj, Service):
            object_type = "service"
        elif isinstance(obj, ServiceNode):
            object_type = "servicenode"
        elif isinstance(obj, Address):
            object_type = "address"
        elif isinstance(obj, AdministrativeDivision):
            object_type = "administrativedivision"
        else:
            return representation

        if object_type == "servicenode":
            ids = self.context["service_node_ids"][str(obj.id)]
            representation["ids"] = ids
            set_service_node_unit_count(ids, representation)
            root_service_node = ServiceNode.get_root_service_node(obj)
            representation["root_service_node"] = RootServiceNodeSerializer(
                root_service_node
            ).data

        # Address IDs are not serialized thus they changes after every import.
        if object_type not in ["address", "servicenode"]:
            representation["id"] = obj.id
        representation["object_type"] = object_type
        names = {}
        if object_type == "address":
            names["fi"] = obj.full_name_fi
            names["sv"] = obj.full_name_sv
            names["en"] = obj.full_name_en
            representation["name"] = names
        else:
            names["fi"] = obj.name_fi
            names["sv"] = obj.name_sv
            names["en"] = obj.name_en
            representation["name"] = names

        if object_type == "unit":
            representation["street_address"] = {
                "fi": obj.street_address_fi,
                "sv": obj.street_address_sv,
                "en": obj.street_address_en,
            }
            if hasattr(obj.municipality, "id"):
                representation["municipality"] = obj.municipality.id
            try:
                shortcomings = obj.accessibility_shortcomings
            except UnitAccessibilityShortcomings.DoesNotExist:
                shortcomings = UnitAccessibilityShortcomings()
            representation["accessibility_shortcoming_count"] = (
                shortcomings.accessibility_shortcoming_count
            )
            representation["contract_type"] = UnitSerializer.get_contract_type(
                self, obj
            )
            representation["department"] = DepartmentSerializer(obj.department).data
            representation["root_department"] = RootDepartmentSerializer(
                obj.root_department
            ).data

        if object_type == "address":
            set_address_fields(obj, representation)

        if object_type == "service":
            set_service_unit_count(obj, representation)
            representation["root_service_node"] = RootServiceNodeSerializer(
                obj.root_service_node
            ).data

        if self.context["geometry"]:
            if hasattr(obj, "geometry"):
                if isinstance(obj, AdministrativeDivision):
                    geometry = obj.geometry.boundary
                else:
                    geometry = obj.geometry
                representation["geometry"] = munigeo_api.geom_to_json(
                    geometry, DEFAULT_SRS
                )
            else:
                representation["geometry"] = None

        if object_type == "unit" or object_type == "address":
            if obj.location:
                representation["location"] = munigeo_api.geom_to_json(
                    obj.location, DEFAULT_SRS
                )

        for include in self.context["include"]:
            try:
                include_object_type, include_field = include.split(".")
            except ValueError:
                raise ParseError(
                    "'include' list elements must be in format: entity.field, e.g.,"
                    " unit.connections."
                )

            if object_type == "unit" and include_object_type == "unit":
                if "connections" in include_field:
                    representation["connections"] = UnitConnectionSerializer(
                        obj.connections, many=True
                    ).data
                elif "department" in include_field:
                    representation["department"] = DepartmentSerializer(
                        obj.department
                    ).data
                elif "municipality" in include_field:
                    representation["municipality"] = obj.municipality.id
                elif "geometry_3d" in include_field:
                    if obj.geometry_3d:
                        representation["geometry_3d"] = munigeo_api.geom_to_json(
                            obj.geometry_3d, DEFAULT_SRS
                        )
                elif "geometry" in include_field:
                    if obj.geometry:
                        representation["geometry"] = munigeo_api.geom_to_json(
                            obj.geometry, DEFAULT_SRS
                        )
                else:
                    if hasattr(obj, include_field):
                        representation[include_field] = getattr(
                            obj, include_field, None
                        )
                    else:
                        raise ParseError(
                            f"Entity {object_type} does not contain a {include_field}"
                            " field."
                        )

        return representation


def build_search_query(query: str):
    result = ""
    query = query.strip(" |&,")
    query = query.replace("\\", "\\\\")
    or_operands = re.split(r"(?:\s*\|+\s*)+", query)

    for or_operand in or_operands:
        # Whitespace, comma and ampersand are all considered AND operators
        and_operands = re.split(r"[\s,&]+", or_operand)
        expression = ""
        for and_operand in and_operands:
            if re.fullmatch(r"'+", and_operand):
                # Skip any operands that are just repeating single-quotes
                continue
            if expression:
                expression += f" & {and_operand}:*"
            else:
                expression = f"{and_operand}:*"

        if not expression:
            continue
        if result:
            result += f" | {expression}"
        else:
            result = expression

    return result


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="q",
            location=OpenApiParameter.QUERY,
            description="The query string used for searching. Searches the"
            " search_columns for the given models. Commas "
            "between words are interpreted as 'and' operator. Words ending with the '|'"
            " sign are interpreted as 'or' "
            "operator.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="type",
            location=OpenApiParameter.QUERY,
            description="Comma separated list of types to search for. Valid values are:"
            " unit, service, servicenode, "
            "address, administrativedivision. If not given defaults to all.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="use_trigram",
            location=OpenApiParameter.QUERY,
            description="Comma separated list of types that will include trigram"
            " results in search if no results are "
            "found. Valid values are: unit, service, servicenode, address,"
            " administrativedivision. If not given "
            "trigram will not be used.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="trigram_threshold",
            location=OpenApiParameter.QUERY,
            description="Threshold value for trigram search. If not given defaults to"
            " 0.15.",
            required=False,
            type=float,
        ),
        OpenApiParameter(
            name="rank_threshold",
            location=OpenApiParameter.QUERY,
            description="Include results with search rank greater than or equal to the"
            " value. If not given defaults to "
            "0.",
            required=False,
            type=float,
        ),
        OpenApiParameter(
            name="use_websearch",
            location=OpenApiParameter.QUERY,
            description="Use websearch_to_tsquery instead of to_tsquery if exclusion"
            " rules are defined for the search.",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="geometry",
            location=OpenApiParameter.QUERY,
            description="Display geometry of the search result. If not given defaults"
            " to false.",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="order_units_by_num_services",
            location=OpenApiParameter.QUERY,
            description="Order units by number of services. If not given defaults to"
            " true.",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="order_units_by_provider_type",
            location=OpenApiParameter.QUERY,
            description="Order units by provider type. If not given defaults to true.",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="include",
            location=OpenApiParameter.QUERY,
            description="Comma separated list of fields to include in the response."
            " Format: entity.field, e.g., "
            "unit.connections.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="sql_query_limit",
            location=OpenApiParameter.QUERY,
            description="Limit the number of results in the search query.",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="unit_limit",
            location=OpenApiParameter.QUERY,
            description="Limit the number of units in the search results.",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="service_limit",
            location=OpenApiParameter.QUERY,
            description="Limit the number of services in the search results.",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="servicenode_limit",
            location=OpenApiParameter.QUERY,
            description="Limit the number of service nodes in the search results.",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="administrativedivision_limit",
            location=OpenApiParameter.QUERY,
            description="Limit the number of administrative divisions in the search"
            " results.",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="address_limit",
            location=OpenApiParameter.QUERY,
            description="Limit the number of addresses in the search results.",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="language",
            location=OpenApiParameter.QUERY,
            description="The language to be used in the search. If not given defaults"
            " to Finnish. Format: fi, sv, en.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="bbox",
            location=OpenApiParameter.QUERY,
            description="Bounding box in the format 'left,bottom,right,top'.",
            required=False,
            type=str,
        ),
    ],
    description="Search for units, services, service nodes, addresses and"
    " administrative divisions.",
)
class SearchViewSet(GenericAPIView):
    queryset = Unit.objects.all()

    def get(self, request):
        model_limits = {}
        show_only_address = False
        units_order_list = []
        for model in list(QUERY_PARAM_TYPE_NAMES):
            model_limits[model] = DEFAULT_MODEL_LIMIT_VALUE

        params = self.request.query_params
        q_val = params.get("q", "").strip() or params.get("input", "").strip()
        if not q_val:
            raise ParseError("Supply search terms with 'q=' ' or input=' '")

        if not re.match(r"^[\w\såäö.,'+&|-]+$", q_val):
            raise ParseError(
                "Invalid search terms, only letters, numbers, spaces and .,'+-&|"
                " allowed."
            )

        types_str = ",".join([elem for elem in QUERY_PARAM_TYPE_NAMES])
        types = params.get("type", types_str).split(",")
        if "use_trigram" in self.request.query_params:
            use_trigram = (
                self.request.query_params["use_trigram"].lower().strip().split(",")
            )
        else:
            use_trigram = ""

        if "trigram_threshold" in params:
            try:
                trigram_threshold = float(params.get("trigram_threshold"))
            except ValueError:
                raise ParseError("'trigram_threshold' needs to be of type float.")
        else:
            trigram_threshold = DEFAULT_TRIGRAM_THRESHOLD

        if "rank_threshold" in params:
            try:
                rank_threshold = float(params.get("rank_threshold"))
            except ValueError:
                raise ParseError("'rank_threshold' needs to be of type float.")
        else:
            rank_threshold = DEFAULT_RANK_THRESHOLD

        if "use_websearch" in params:
            try:
                use_websearch = strtobool(params["use_websearch"])
            except ValueError:
                raise ParseError("'use_websearch' needs to be a boolean")
        else:
            use_websearch = True

        if "geometry" in params:
            try:
                show_geometry = strtobool(params["geometry"])
            except ValueError:
                raise ParseError("'geometry' needs to be a boolean")
        else:
            show_geometry = False

        if "order_units_by_num_services" in params:
            try:
                order_units_by_num_services = strtobool(
                    params["order_units_by_num_services"]
                )
            except ValueError:
                raise ParseError("'order_units_by_num_services' needs to be a boolean")
        else:
            order_units_by_num_services = True

        if order_units_by_num_services:
            units_order_list.append("-num_services")

        if "order_units_by_provider_type" in params:
            try:
                order_units_by_provider_type = strtobool(
                    params["order_units_by_provider_type"]
                )
            except ValueError:
                raise ParseError("'order_units_by_provider_type' needs to be a boolean")
        else:
            order_units_by_provider_type = True

        if order_units_by_provider_type:
            units_order_list.append("provider_type")

        if "include" in params:
            include_fields = params["include"].split(",")
        else:
            include_fields = []
        # Limit number of results in searchquery.
        if "sql_query_limit" in params:
            try:
                sql_query_limit = int(params.get("sql_query_limit"))
            except ValueError:
                raise ParseError("'sql_query_limit' need to be of type integer.")
        else:
            sql_query_limit = DEFAULT_SEARCH_SQL_LIMIT_VALUE
        # Read values for limit values for each model
        for type_name in QUERY_PARAM_TYPE_NAMES:
            param_name = f"{type_name}_limit"
            if param_name in params:
                try:
                    model_limits[type_name] = int(params.get(param_name))
                except ValueError:
                    raise ParseError(f"{param_name} need to be of type integer.")
            else:
                model_limits[type_name] = DEFAULT_MODEL_LIMIT_VALUE

        language_short = params.get("language", "fi").strip()
        if language_short not in LANGUAGES:
            raise ParseError(
                "Invalid language argument, valid choices are: "
                + "".join([k + ", " for k, v in LANGUAGES.items()])[:-2]
            )

        config_language = LANGUAGES[language_short]

        all_operands = re.split(r"[\s|&,]+", q_val)
        if has_exclusion_word_in_query(all_operands, language_short):
            return Response(
                f"Search query {q_val} would return too many results",
                status=status.HTTP_400_BAD_REQUEST,
            )
        search_query_str = build_search_query(q_val)

        search_fn = "to_tsquery"
        if use_websearch:
            # NOTE: The check is done on the last operand only on purpose.
            # This is a fix for some old edge case.
            exclusions = self.get_search_exclusions(all_operands[-1])
            if exclusions:
                search_fn = "websearch_to_tsquery"
                search_query_str += f" {exclusions}"

        # This is ~100 times faster than using Django's SearchRank and allows searching
        # using wildcard "|*" and by ranking gives better results, e.g. extra fields
        # weight is counted.
        sql = f"""
            SELECT * from (
                SELECT id, type_name, name_{language_short}, ts_rank_cd(search_column_{language_short}, search_query)
                AS rank FROM search_view, {search_fn}('{config_language}', %s) search_query
                WHERE search_query @@ search_column_{language_short}
                ORDER BY rank DESC LIMIT {sql_query_limit}
            ) AS sub_query where sub_query.rank >= {rank_threshold};
        """  # noqa: E501

        cursor = connection.cursor()
        try:
            cursor.execute(sql, [search_query_str])
        except Exception as e:
            logger.error(f"Error in search query: {e}", exc_info=e)
            raise ParseError("Search query failed.")
        # Note, fetchall() consumes the results and once called returns None.
        all_results = cursor.fetchall()
        all_ids = get_all_ids_from_sql_results(all_results)

        unit_ids = all_ids["Unit"]
        service_ids = all_ids["Service"]
        service_node_ids = get_service_node_results(all_results)

        administrative_division_ids = all_ids["AdministrativeDivision"]
        address_ids = all_ids["Address"]

        if "service" in types:
            preserved = get_preserved_order(service_ids)
            services_qs = Service.objects.filter(id__in=service_ids).order_by(preserved)
            if not services_qs and "service" in use_trigram:
                services_qs = get_trigram_results(
                    Service,
                    "services_service",
                    "name_" + language_short,
                    q_val,
                    threshold=trigram_threshold,
                )

            services_qs = services_qs.annotate(num_units=Count("units")).order_by(
                "-num_units"
            )
            # order_by() call makes duplicate rows appear distinct. This is solved by
            # fetching the ids and filtering a new queryset using them
            ids = list(services_qs.values_list("id", flat=True))
            # remove duplicates from list
            ids = list(dict.fromkeys(ids))
            preserved = get_preserved_order(ids)
            services_qs = Service.objects.filter(id__in=ids).order_by(preserved)
            services_qs = services_qs[: model_limits["service"]]
        else:
            services_qs = Service.objects.none()

        if "unit" in types:
            if unit_ids:
                preserved = get_preserved_order(unit_ids)
                units_qs = Unit.objects.filter(id__in=unit_ids).order_by(preserved)
            else:
                units_qs = Unit.objects.none()

            if not units_qs.exists():
                show_only_address = True
            if not units_qs and "unit" in use_trigram:
                units_qs = get_trigram_results(
                    Unit,
                    "services_unit",
                    "name_" + language_short,
                    q_val,
                    threshold=trigram_threshold,
                )

            units_qs = units_qs.all().distinct()
            if "municipality" in self.request.query_params:
                municipalities = (
                    self.request.query_params["municipality"].lower().strip().split(",")
                )
                if len(municipalities) > 0:
                    units_qs = units_qs.filter(municipality_id__in=municipalities)
            if "organization" in self.request.query_params:
                organizations = (
                    self.request.query_params["organization"].lower().strip().split(",")
                )
                if len(organizations) > 0:
                    units_qs = units_qs.filter(root_department__uuid__in=organizations)
            if "service" in self.request.query_params:
                services = self.request.query_params["service"].strip().split(",")
                if services[0]:
                    units_qs = units_qs.filter(services__in=services)

            if "bbox" in self.request.query_params:
                bbox = self.request.query_params["bbox"]
                if "bbox_srid" in self.request.query_params:
                    bbox_srid = self.request.query_params["bbox_srid"]
                else:
                    bbox_srid = get_default_srid()
                ref = SpatialReference(bbox_srid)
                bbox_filter = munigeo_api.build_bbox_filter(ref, bbox, "location")
                units_qs = units_qs.filter(**bbox_filter)

            if units_order_list:
                units_qs = units_qs.annotate(num_services=Count("services")).order_by(
                    *units_order_list
                )

            units_qs = units_qs[: model_limits["unit"]]
        else:
            units_qs = Unit.objects.none()

        if "administrativedivision" in types:
            administrative_divisions_qs = AdministrativeDivision.objects.filter(
                id__in=administrative_division_ids
            )
            if (
                not administrative_divisions_qs
                and "administrativedivision" in use_trigram
            ):
                administrative_divisions_qs = get_trigram_results(
                    AdministrativeDivision,
                    "munigeo_administrativedivision",
                    "name_" + language_short,
                    q_val,
                    threshold=trigram_threshold,
                )
            administrative_divisions_qs = administrative_divisions_qs[
                : model_limits["administrativedivision"]
            ]
        else:
            administrative_divisions_qs = AdministrativeDivision.objects.none()
        if "servicenode" in types:
            query_ids = [id[0] for id in service_node_ids.values()]
            service_nodes_qs = ServiceNode.objects.filter(id__in=query_ids)
            if not service_nodes_qs and "servicenode" in use_trigram:
                service_nodes_qs = get_trigram_results(
                    ServiceNode,
                    "services_servicenode",
                    "name_" + language_short,
                    q_val,
                    threshold=trigram_threshold,
                )
                service_nodes_qs = service_nodes_qs[: model_limits["servicenode"]]
        else:
            service_nodes_qs = ServiceNode.objects.none()

        if "address" in types:
            addresses_qs = Address.objects.filter(id__in=address_ids)
            if not addresses_qs and "address" in use_trigram:
                addresses_qs = get_trigram_results(
                    Address,
                    "munigeo_address",
                    "full_name_" + language_short,
                    q_val,
                    threshold=trigram_threshold,
                )
            if "municipality" in self.request.query_params:
                municipalities = (
                    self.request.query_params["municipality"].lower().strip().split(",")
                )
                if len(municipalities) > 0:
                    addresses_qs = addresses_qs.filter(
                        municipality_id__in=municipalities
                    )
            addresses_qs = addresses_qs[: model_limits["address"]]
            # Use naturalsort function that is migrated to munigeo to
            # sort the addresses.
            if len(addresses_qs) > 0:
                ids = [str(addr.id) for addr in addresses_qs]
                # create string containing ids in format (1,4,2)
                ids_str = ",".join(ids)
                ids_str = f"({ids_str})"
                sql = f"""
                    select id from munigeo_address where id in {ids_str}
                    order by naturalsort(full_name_{language_short}) asc;
                """
                cursor = connection.cursor()
                cursor.execute(sql)
                addresses = cursor.fetchall()
                # addresses are in format e.g. [(12755,), (4067,)], remove comma and
                # parenthesis
                ids = [re.sub(r"[(,)]", "", str(a)) for a in addresses]
                preserved = get_preserved_order(ids)
                addresses_qs = Address.objects.filter(id__in=ids).order_by(preserved)
                # if no units has been found without trigram search and addresses are
                # found,
                # do not return any units, thus they might confuse in the results.
                if addresses_qs.exists() and show_only_address:
                    units_qs = Unit.objects.none()
        else:
            addresses_qs = Address.objects.none()

        if logger.level <= logging.DEBUG:
            logger.debug(connection.queries)
            queries_time = sum([float(s["time"]) for s in connection.queries])
            logger.debug(
                f"Search queries total execution time: {queries_time}"
                f" Num queries: {len(connection.queries)}"
            )
            reset_queries()

        queryset = list(
            chain(
                units_qs,
                services_qs,
                service_nodes_qs,
                administrative_divisions_qs,
                addresses_qs,
            )
        )
        page = self.paginate_queryset(queryset)
        serializer = SearchSerializer(
            page,
            many=True,
            context={
                "service_node_ids": service_node_ids,
                "include": include_fields,
                "geometry": show_geometry,
            },
        )
        return self.get_paginated_response(serializer.data)

    def get_search_exclusions(self, q):
        rule = ExclusionRule.objects.filter(word__iexact=q).first()
        if rule:
            return rule.exclusion
        return ""
