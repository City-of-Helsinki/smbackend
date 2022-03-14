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
 management script.
"""
import logging
import re
from distutils.util import strtobool
from itertools import chain

from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
# from django.contrib.postgres.search import TrigramSimilarity
from django.db import connection, reset_queries
from django.db.models import Case, Count, When
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

logger = logging.getLogger("search")
LANGUAGES = {k: v.lower() for k, v in settings.LANGUAGES}
DEFAULT_SRS = SpatialReference(4326)
SEARCHABLE_MODEL_TYPE_NAMES = (
    "Unit",
    "Service",
    "ServiceNode",
    "AdministrativeDivision",
    "Address",
)
QUERY_PARAM_TYPE_NAMES = [m.lower() for m in SEARCHABLE_MODEL_TYPE_NAMES]
DEFAULT_MODEL_LIMIT_VALUE = None  # None will slice to the end of list
# The limit value for the search query that search the search_view. "NULL" = no limit
DEFAULT_SEARCH_SQL_LIMIT_VALUE = "NULL"
DEFAULT_TRIGRAM_THRESHOLD = 0.15


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
        # Address IDs are not serialized thus they changes after every import.
        if object_type != "address":
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
                representation["street_address"] = getattr(obj, "street_address")
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
                representation["number"] = getattr(obj, "number", "")
                representation["number_end"] = getattr(obj, "number_end", "")
                representation["letter"] = getattr(obj, "letter", "")
                representation["modified_at"] = getattr(obj, "modified_at", "")
                municipality = {
                    "id": getattr(obj.street, "municipality_id", ""),
                    "name": {},
                }
                municipality["name"]["fi"] = getattr(
                    obj.street.municipality, "name_fi", ""
                )
                municipality["name"]["sv"] = getattr(
                    obj.street.municipality, "name_sv", ""
                )
                representation["municipality"] = municipality
                street = {"name": {}}
                street["name"]["fi"] = getattr(obj.street, "name_fi", "")
                street["name"]["sv"] = getattr(obj.street, "name_sv", "")
                representation["street"] = street

            if object_type == "unit" or object_type == "address":
                if obj.location:
                    representation["location"] = munigeo_api.geom_to_json(
                        obj.location, DEFAULT_SRS
                    )

        return representation


def get_ids_from_sql_results(all_results, type="Unit"):
    """
    Returns a list of ids by the give type.
    """
    ids = []
    for row in all_results:
        if row[1] == type:
            # Id is the first col and in format 42_type.
            ids.append(row[0].split("_")[1])
    return ids


def get_all_ids_from_sql_results(all_results):
    """
    Returns a dict with the model names as keys and the
    object ids of the model as values.
    """
    ids = {}
    for t in SEARCHABLE_MODEL_TYPE_NAMES:
        ids[t] = []
    for row in all_results:
        ids[row[1]].append(row[0].split("_")[1])
    return ids


def get_preserved_order(ids):
    """
    Returns a Case expression that can be used in the order_by method,
    ordering will be equal to the order of ids in the ids list.
    """
    if ids:
        return Case(*[When(id=id, then=pos) for pos, id in enumerate(ids)])
    else:
        return Case()


# def get_trigram_results(model, field, q_val, threshold=0.1):
#     trigm = (
#         model.objects.annotate(
#             similarity=TrigramSimilarity(field, q_val),
#         )
#         .filter(similarity__gt=threshold)
#         .order_by("-similarity")
#     )
#     ids = trigm.values_list("id", flat=True)
#     if ids:
#         preserved = get_preserved_order(ids)
#         return model.objects.filter(id__in=ids).order_by(preserved)
#     else:
#         return model.objects.none()


def get_trigram_results(
    model, model_name, field, q_val, threshold=DEFAULT_TRIGRAM_THRESHOLD
):
    sql = f"""SELECT id, similarity({field}, '{q_val}') AS sml
        FROM {model_name}
        WHERE  similarity({field}, '{q_val}') >= {threshold}
        ORDER BY sml DESC;
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    all_results = cursor.fetchall()

    ids = [row[0] for row in all_results]
    objs = model.objects.filter(id__in=ids)
    return objs


class SearchViewSet(GenericAPIView):
    queryset = Unit.objects.all()

    def get(self, request):
        model_limits = {}
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
        q_vals = [s.strip() for s in q_vals]
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
        service_node_ids = all_ids["ServiceNode"]
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
            service_nodes_qs = ServiceNode.objects.filter(id__in=service_node_ids)
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
            page, many=True, context={"extended_serializer": extended_serializer}
        )
        return self.get_paginated_response(serializer.data)
