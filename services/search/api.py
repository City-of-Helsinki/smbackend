"""
Brief explanation how full text search is implemented in the smbacked.
- Currently search is performed to following models, Unit, Service, 
munigeo_Address, munigeo_Administrative_division.
- For every model that is include in the search a column named
 search_column of type SeaarchVector is added. This is also defined as a Gindex. 
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
from itertools import chain
import re
import logging
from collections import namedtuple
from distutils.util import strtobool
from django.contrib.postgres.search import TrigramSimilarity
from django.contrib.gis.gdal import SpatialReference
from django.db.models import Case, When
from django.conf import settings
from django.db import connection, reset_queries
from django.db.models import Count
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import ParseError
from rest_framework import serializers
from munigeo import api as munigeo_api
from munigeo.models import Address, AdministrativeDivision, Street
from services.api import TranslatedModelSerializer, UnitSerializer
from services.models import (
    Service,
    Unit,
    Department,
    UnitAccessibilityShortcomings,
)

logger = logging.getLogger("search")
LANGUAGES = {k: v.lower() for k, v in settings.LANGUAGES}
DEFAULT_SRS = SpatialReference(settings.DEFAULT_SRID)
SEARCHABLE_MODEL_TYPE_NAMES = ("Unit", "Service", "AdministrativeDivision", "Address")
QUERY_PARAM_TYPE_NAMES = [m.lower() for m in SEARCHABLE_MODEL_TYPE_NAMES]
# Note, default limit should be big enough, otherwise quality of results will drop..
DEFAULT_MODEL_LIMIT_VALUE = 5
# The limit value for the search query that search the search_view.
DEFAULT_SEARCH_SQL_LIMIT_VALUE = 100


class DepartmentSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "street_address", "municipality"]


class ExtendedSearchResultUnitSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Unit
        fields = [
            "id",
            "name",
            "street_address",
            "municipality",
        ]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        if obj.location:
            representation["location"] = munigeo_api.geom_to_json(
                obj.location, DEFAULT_SRS
            )

        try:
            shortcomings = obj.accessibility_shortcomings
        except UnitAccessibilityShortcomings.DoesNotExist:
            shortcomings = UnitAccessibilityShortcomings()
        representation[
            "accessibility_shortcoming_count"
        ] = shortcomings.accessibility_shortcoming_count
        representation["contract_type"] = UnitSerializer.get_contract_type(self, obj)
        representation["department"] = DepartmentSerializer(obj.department).data
        return representation


class SearchResultUnitSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Unit
        fields = ["id", "name"]


class SearchResultServiceSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Service
        fields = ["id", "name"]


class SearchResultAdministrativeDivisionSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = AdministrativeDivision
        fields = ["id", "name"]


class SearchResultAddressSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Address
        fields = ["id", "full_name"]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        if obj.location:
            representation["location"] = munigeo_api.geom_to_json(
                obj.location, DEFAULT_SRS
            )
        return representation


class ExtendedSearchResultAddressSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Address
        fields = ["id", "full_name"]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        if obj.location:
            representation["location"] = munigeo_api.geom_to_json(
                obj.location, DEFAULT_SRS
            )
        return representation


class SearchSerializer(serializers.Serializer):

    units = SearchResultUnitSerializer(many=True)
    services = SearchResultServiceSerializer(many=True)
    addresses = SearchResultAddressSerializer(many=True)
    administrative_divisions = SearchResultAdministrativeDivisionSerializer(many=True)


class ExtendedSearchSerializer(serializers.Serializer):

    units = ExtendedSearchResultUnitSerializer(many=True)
    services = SearchResultServiceSerializer(many=True)
    addresses = ExtendedSearchResultAddressSerializer(many=True)
    administrative_divisions = SearchResultAdministrativeDivisionSerializer(many=True)


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


def get_trigram_results(model, field, q_val, threshold=0.1):
    trigm = (
        model.objects.annotate(
            similarity=TrigramSimilarity(field, q_val),
        )
        .filter(similarity__gt=threshold)
        .order_by("-similarity")
    )
    ids = trigm.values_list("id", flat=True)
    if ids:
        preserved = get_preserved_order(ids)
        return model.objects.filter(id__in=ids).order_by(preserved)
    else:
        return model.objects.none()


class SearchViewSet(GenericAPIView):
    queryset = Unit.objects.all()

    def get(self, request):
        model_limits = {}
        units_order_list = ["provider_type"]
        extended_serializer = True
        for model in list(QUERY_PARAM_TYPE_NAMES):
            model_limits[model] = DEFAULT_MODEL_LIMIT_VALUE
        SearchResult = namedtuple(
            "SearchResult",
            (
                "services",
                "units",
                "administrative_divisions",
                "addresses",
            ),
        )
        params = self.request.query_params
        q_val = params.get("q", "").strip()
        if not q_val:
            raise ParseError("Supply search terms with 'q=' '")

        types_str = ",".join([elem for elem in QUERY_PARAM_TYPE_NAMES])
        types = params.get("type", types_str).split(",")
        if "use_trigram" in params:
            try:
                use_trigram = strtobool(params["use_trigram"])
            except ValueError:
                raise ParseError("'use_trigram' needs to be a boolean")
        else:
            use_trigram = True

        if "extended_serializers" in params:
            try:
                extended_serializer = strtobool(params["extended_serializers"])
            except ValueError:
                raise ParseError("'extended_serializers' needs to be a boolean")

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
        q_vals = re.split(",\s+|\s+", q_val)
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
        SELECT id, type_name, name_{language_short}, ts_rank_cd(search_column, search_query) AS rank
        FROM search_view, to_tsquery('{config_language}','{search_query_str}') search_query
        WHERE search_query @@ search_column 
        ORDER BY rank DESC LIMIT {sql_query_limit};
        """

        cursor = connection.cursor()
        cursor.execute(sql)
        # Note, fetchall() consumes the results and once called returns None.
        all_results = cursor.fetchall()
        all_ids = get_all_ids_from_sql_results(all_results)
        unit_ids = all_ids["Unit"]
        service_ids = all_ids["Service"]
        administrative_division_ids = all_ids["AdministrativeDivision"]
        address_ids = all_ids["Address"]

        if "service" in types:
            preserved = get_preserved_order(service_ids)
            services_qs = Service.objects.filter(id__in=service_ids).order_by(preserved)
            if not services_qs and use_trigram:
                services_qs = get_trigram_results(
                    Service, "name_" + language_short, q_val
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
            units_from_services = Unit.objects.filter(
                services__in=service_ids, public=True
            )
            # Add units which are associated with the services found.
            units_qs = units_from_services | units_qs
            # Combine units from services and the units_qs.
            ids1 = list(units_from_services.values_list("id", flat=True))
            ids2 = list(units_qs.values_list("id", flat=True))
            ids1 = []
            ids = ids1 + ids2
            units_qs = Unit.objects.filter(id__in=ids)

            if not units_qs and use_trigram:
                units_qs = get_trigram_results(Unit, "name_" + language_short, q_val)

            units_qs = units_qs.all().distinct()
            if "municipality" in self.request.query_params:
                municipalities = (
                    self.request.query_params["municipality"].lower().strip().split(",")
                )
                if municipalities[0]:
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
            administrative_division_qs = AdministrativeDivision.objects.filter(
                id__in=administrative_division_ids
            )
            if not administrative_division_qs and use_trigram:
                administrative_division_qs = get_trigram_results(
                    AdministrativeDivision, "name_" + language_short, q_val
                )
            administrative_division_qs = administrative_division_qs[
                : model_limits["administrativedivision"]
            ]
        else:
            administrative_division_qs = AdministrativeDivision.objects.none()

        if "address" in types:
            address_qs = Address.objects.filter(id__in=address_ids)
            if not address_qs and use_trigram:
                address_qs = get_trigram_results(
                    Address, "full_name_" + language_short, q_val
                )
            address_qs = address_qs[: model_limits["address"]]
        else:
            address_qs = Address.objects.none()

        search_results = SearchResult(
            units=units_qs,
            services=services_qs,
            administrative_divisions=administrative_division_qs,
            addresses=address_qs,
        )

        if extended_serializer:
            serializer = ExtendedSearchSerializer(search_results)
        else:
            serializer = SearchSerializer(search_results)

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
                administrative_division_qs,
                address_qs,
            )
        )

        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(serializer.data)
