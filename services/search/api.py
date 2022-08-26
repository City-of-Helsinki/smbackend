"""
Brief explanation how full text search is implemented in the smbacked.
- Currently search is performed to following models, Unit, Service,
munigeo_Address, munigeo_Administrative_division.
- For every model that is include in the search a search column is added
for every language of type SearchVector. These are also defined as a Gindex.
 The models that are searched also implements a function called get_search_column_indexing
  where the name, configuration(language) and weight of the columns that will be indexed
  are defined. This function is used by the indexing script and signals when
  the search_column is populated.
- A view called search_view is created and it contains the search_columns of the models
and a couple auxilary columns: id. type_name and name. This view is created by a
raw SQL migration 008X_create_search_view.py.
- The search if performed by quering the views search_columns.
- For models included in the search a post_save signal is connected and the
  search_column is updated when they are saved.
- The search_columns can be manually updated with  the index_search_columns
and emptied with the empty_search_columns management script.
"""
import logging
import re
from distutils.util import strtobool
from itertools import chain

from django.db import connection, reset_queries
from django.db.models import Count
from munigeo import api as munigeo_api
from munigeo.models import Address, AdministrativeDivision
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView

from services.api import TranslatedModelSerializer, UnitSerializer
from services.models import (
    Department,
    Service,
    ServiceNode,
    Unit,
    UnitAccessibilityShortcomings,
)

from .constants import (
    DEFAULT_MODEL_LIMIT_VALUE,
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
    set_address_fields,
    set_service_node_unit_count,
    set_service_unit_count,
)

logger = logging.getLogger("search")


class RootServiceNodeSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = ServiceNode
        fields = ["id", "name"]


class DepartmentSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "street_address", "municipality"]


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
            representation["id"] = getattr(obj, "id")
        representation["object_type"] = object_type
        names = {}
        if object_type == "address":
            names["fi"] = getattr(obj, "full_name_fi")
            names["sv"] = getattr(obj, "full_name_sv")
            names["en"] = getattr(obj, "full_name_en")
            representation["name"] = names
        else:
            names["fi"] = getattr(obj, "name_fi")
            names["sv"] = getattr(obj, "name_sv")
            names["en"] = getattr(obj, "name_en")
            representation["name"] = names

        if self.context["extended_serializer"]:
            if object_type == "unit":
                representation["street_address"] = {
                    "fi": getattr(obj, "street_address_fi"),
                    "sv": getattr(obj, "street_address_sv"),
                    "en": getattr(obj, "street_address_en"),
                }
                if hasattr(obj.municipality, "id"):
                    representation["municipality"] = getattr(obj.municipality, "id")
                try:
                    shortcomings = obj.accessibility_shortcomings
                except UnitAccessibilityShortcomings.DoesNotExist:
                    shortcomings = UnitAccessibilityShortcomings()
                representation[
                    "accessibility_shortcoming_count"
                ] = shortcomings.accessibility_shortcoming_count
                representation["contract_type"] = UnitSerializer.get_contract_type(
                    self, obj
                )
                representation["department"] = DepartmentSerializer(obj.department).data
                if obj.geometry:
                    representation["geometry"] = munigeo_api.geom_to_json(
                        obj.geometry, DEFAULT_SRS
                    )
                else:
                    representation["geometry"] = None

            if object_type == "address":
                set_address_fields(obj, representation)

            if object_type == "service":
                set_service_unit_count(obj, representation)
                representation["root_service_node"] = RootServiceNodeSerializer(
                    obj.root_service_node
                ).data

            if object_type == "unit" or object_type == "address":
                if obj.location:
                    representation["location"] = munigeo_api.geom_to_json(
                        obj.location, DEFAULT_SRS
                    )
        return representation


class SearchViewSet(GenericAPIView):
    queryset = Unit.objects.all()

    def get(self, request):
        model_limits = {}
        show_only_address = False
        units_order_list = ["provider_type"]
        extended_serializer = True
        for model in list(QUERY_PARAM_TYPE_NAMES):
            model_limits[model] = DEFAULT_MODEL_LIMIT_VALUE

        params = self.request.query_params
        q_val = params.get("q", "").strip()
        if not q_val:
            raise ParseError("Supply search terms with 'q=' '")

        types_str = ",".join([elem for elem in QUERY_PARAM_TYPE_NAMES])
        types = params.get("type", types_str).split(",")
        if "use_trigram" in self.request.query_params:
            use_trigram = (
                self.request.query_params["use_trigram"].lower().strip().split(",")
            )
        else:
            use_trigram = "unit"

        if "trigram_threshold" in params:
            try:
                trigram_threshold = float(params.get("trigram_threshold"))
            except ValueError:
                raise ParseError("'trigram_threshold' need to be of type float.")
        else:
            trigram_threshold = DEFAULT_TRIGRAM_THRESHOLD

        if "extended_serializer" in params:
            try:
                extended_serializer = strtobool(params["extended_serializer"])
            except ValueError:
                raise ParseError("'extended_serializer' needs to be a boolean")

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
        search_query_str = None  # Used in the raw sql
        # Build conditional query string that is used in the SQL query.
        # split my "," or whitespace
        q_vals = re.split(r",\s+|\s+", q_val)
        q_vals = [s.strip().replace("'", "") for s in q_vals]
        for q in q_vals:
            if search_query_str:
                # if ends with "|"" make it a or
                if q[-1] == "|":
                    search_query_str += f"| {q[:-1]}:*"
                # else make it an and.
                else:
                    search_query_str += f"& {q}:*"
            else:
                search_query_str = f"{q}:*"

        # This is ~100 times faster than using Djangos SearchRank and allows searching using wildard "|*"
        # and by rankig gives better results, e.g. extra fields weight is counted.
        sql = f"""
        SELECT id, type_name, name_{language_short}, ts_rank_cd(search_column_{language_short}, search_query)
        AS rank FROM search_view, to_tsquery('{config_language}','{search_query_str}') search_query
        WHERE search_query @@ search_column_{language_short}
        ORDER BY rank DESC LIMIT {sql_query_limit};
        """

        cursor = connection.cursor()
        cursor.execute(sql)
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
                "-units__count"
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
            if "service" in self.request.query_params:
                services = self.request.query_params["service"].strip().split(",")
                if services[0]:
                    units_qs = units_qs.filter(services__in=services)
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
                        street__municipality_id__in=municipalities
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
                # addresses are in format e.g. [(12755,), (4067,)], remove comma and parenthesis
                ids = [re.sub(r"[(,)]", "", str(a)) for a in addresses]
                preserved = get_preserved_order(ids)
                addresses_qs = Address.objects.filter(id__in=ids).order_by(preserved)
                # if no units has been found without trigram search and addresses are found,
                # do not return any units, thus they might confuse in the results.
                if addresses_qs.exists() and show_only_address:
                    units_qs = Unit.objects.none()
        else:
            addresses_qs = Address.objects.none()

        if logger.level <= logging.DEBUG:
            logger.debug(connection.queries)
            queries_time = sum([float(s["time"]) for s in connection.queries])
            logger.debug(
                f"Search queries total execution time: {queries_time} Num queries: {len(connection.queries)}"
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
                "extended_serializer": extended_serializer,
                "service_node_ids": service_node_ids,
            },
        )
        return self.get_paginated_response(serializer.data)
