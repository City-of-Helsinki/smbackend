import re
from collections import namedtuple
from distutils.util import strtobool
from itertools import chain
from pprint import pprint as pp

from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.db import connection, reset_queries
from django.db.models import Case, When
from django.db.models.query_utils import Q
from munigeo import api as munigeo_api
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView

from services.api import (
    SearchSerializer,
    ServiceNodeSerializer,
    ServiceSerializer,
    TranslatedModelSerializer,
    UnitSerializer,
)
from services.models import SearchView, Service, ServiceNode, Unit

BENCHMARK = True
LANGUAGES = {k: v.lower() for k, v in settings.LANGUAGES}
DEFAULT_SRS = SpatialReference(settings.DEFAULT_SRID)


class SearchResultUnitSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Unit
        fields = ["id", "name"]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        if obj.location:
            representation["location"] = munigeo_api.geom_to_json(
                obj.location, DEFAULT_SRS
            )
        return representation


class SearchResultServiceSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Service
        fields = ["id", "name"]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        # Todo, maybe? unit_count per municipality. Does not work with turku data.
        representation["unit_count"] = Unit.objects.filter(services=obj.id).count()
        return representation


class SearchResultServiceNodeSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = ServiceNode
        fields = ["id", "name"]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["unit_count"] = dict(
            municipality=dict(
                (
                    (x.division.name_fi.lower() if x.division else "_unknown", x.count)
                    for x in obj.unit_counts.all()
                )
            )
        )
        total = 0
        for _, part in representation["unit_count"]["municipality"].items():
            total += part
        representation["unit_count"]["total"] = total
        return representation


class SearchSerializer(serializers.Serializer):
    units = SearchResultUnitSerializer(many=True)
    # units = UnitSerializer(many=True)
    services = SearchResultServiceSerializer(many=True)
    service_nodes = SearchResultServiceNodeSerializer(many=True)


class SuggestionSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    type = serializers.CharField()
    name = serializers.CharField()
    location = serializers.SerializerMethodField(read_only=True)

    class Meta:
        fields = ["id", "type", "name", "location"]

    def get_location(self, obj):
        if obj["type"] == "Unit":
            unit = Unit.objects.get(id=obj["id"])
            if unit.location:
                return munigeo_api.geom_to_json(unit.location, DEFAULT_SRS)
            else:
                return None
        else:
            return None


def build_dict(all_results):
    results = []
    for row in all_results:
        elem = {}
        elem["id"] = row[0].split("_")[1]
        elem["type"] = row[1]
        elem["name"] = row[2]
        results.append(elem)
    return results


def build_serializable_data(all_results, ids):
    """
    Builds a list of dict elements with id, type and name,
    these can be serialized with the SuggestionSerializer.
    Discards elements that are not in the ids list. The ids list
    contains the ids of the objects that are left after filtering
    with various query parameters.
    """
    results = []
    for row in all_results:
        elem = {}
        elem["id"] = row[0].split("_")[1]
        elem["type"] = row[1]
        elem["name"] = row[2]
        if int(elem["id"]) in ids[elem["type"]]:
            results.append(elem)
    return results


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


class SearchViewSet(GenericAPIView):
    queryset = Unit.objects.all()

    def get(self, request):
        sql_search = False
        SearchResult = namedtuple(
            "SearchResult", ("services", "units", "service_nodes")
        )
        params = self.request.query_params
        q_val = params.get("q", "").strip()
        if "sql" in params:
            try:
                sql_search = strtobool(params["sql"])
            except ValueError:
                raise ParseError("'sql' needs to be a boolean")

        if not q_val:
            raise ParseError("Supply search terms with 'q=' '")
        types = params.get("type", "unit,service,service_node").split(",")

        # Limit number of "suggestions"
        if "limit" in params:
            try:
                limit = int(params.get("limit"))
            except ValueError:
                raise ParseError("'limit' need to be of type integer.")
        else:
            limit = 1000

        language_short = params.get("language", "fi").strip()
        if language_short not in LANGUAGES:
            raise ParseError(
                "Invalid language argument, valid choices are: "
                + "".join([k + ", " for k, v in LANGUAGES.items()])[:-2]
            )

        config_language = LANGUAGES[language_short]
        search_type = "plain"
        search_query_str = None  # Used in the raw sql
        search_query = None  # Used with djangos filter
        # Build conditional searchquery.
        q_vals = re.split(",|\s+", q_val)
        for q in q_vals:

            if sql_search:
                if search_query_str:
                    # If word ends with "."  make it and(&), i.e. must be included.
                    if q[-1] == ".":
                        search_query_str += f"& {q}:*"
                    else:
                        search_query_str += f"& {q}:*"
                else:
                    search_query_str = f"{q}:*"
            else:
                if search_query:
                    if q[-1] == ".":
                        search_query &= SearchQuery(
                            q, config=config_language, search_type=search_type
                        )
                    else:
                        search_query &= SearchQuery(
                            q, config=config_language, search_type=search_type
                        )
                else:
                    search_query = SearchQuery(
                        q, config=config_language, search_type=search_type
                    )

        if sql_search:
            # This is ~100 times faster than using Djangos SearchRank
            # and by rankig gives better results, e.g. description fields weight is counted
            sql = f"""
            SELECT id, type_name, name_{language_short}, ts_rank_cd(search_column, search_query) AS rank
            FROM search_view, to_tsquery('{config_language}','{search_query_str}') search_query
            WHERE search_query @@ search_column ORDER BY rank DESC LIMIT {limit};
            """
            cursor = connection.cursor()
            cursor.execute(sql)
            # Note fetchall() consumes the results and once called returns None.
            all_results = cursor.fetchall()
            unit_ids = get_ids_from_sql_results(all_results, type="Unit")
            service_ids = get_ids_from_sql_results(all_results, type="Service")
            service_node_ids = get_ids_from_sql_results(all_results, "ServiceNode")

        else:
            # NOTE, Using dangos search is ~100 times slower than raw sql
            queryset = (
                SearchView.objects.annotate(
                    rank=SearchRank("search_column", search_query)
                )
                .filter(rank__gt=0.0)
                .distinct()
                .order_by("-rank")
            )
            service_ids = []
            unit_ids = []
            service_node_ids = []
            # Get the IDs from the queryset in one loop.
            # Filtering by types causes the queryset to be evaluated for every filter call
            # and is slower.
            for elem in queryset.all()[:limit]:
                if elem.type_name == "Service":
                    service_ids.append(elem.id.replace("service_", ""))
                elif elem.type_name == "Unit":
                    unit_ids.append(elem.id.replace("unit_", ""))
                elif elem.type_name == "ServiceNode":
                    service_node_ids.append(elem.id.replace("servicenode_", ""))

        if "service" in types:
            services_qs = Service.objects.filter(id__in=service_ids)
        else:
            services_qs = Service.objects.none()

        if "unit" in types:
            # units_qs = Unit.objects.filter(id__in=unit_ids, public=True)
            # preserve the order in the unit_ids list.
            preserved = Case(
                *[When(id=id, then=pos) for pos, id in enumerate(unit_ids)]
            )
            units_qs = Unit.objects.filter(id__in=unit_ids).order_by(preserved)
            units_from_services = Unit.objects.filter(
                services__in=service_ids, public=True
            )
            # Add units which are associated with the services found.
            if q_val:
                # units_qs = units_qs.union(units_from_services)
                units_qs = units_from_services | units_qs
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
        else:
            units_qs = Unit.objects.none()

        if "service_node" in types:
            service_nodes_qs = ServiceNode.objects.filter(id__in=service_node_ids)
        else:
            service_nodes_qs = ServiceNode.objects.none()

        if q_val:
            search_results = SearchResult(
                units=units_qs, services=services_qs, service_nodes=service_nodes_qs
            )
            serializer = SearchSerializer(search_results)
            # results = list()
            # for entry in search_results:

            #         item_type = entry.__class__.__name__.lower()
            #         if isinstance(entry, Unit):
            #             serializer = UnitSerializer(entry)
            #         if isinstance(entry, Service):
            #             serializer = ServiceSerializer(entry)
            #         if isinstance(entry, ServiceNode):
            #             serializer = ServiceNodeSerializer(entry)
            #         results.append({'item_type': item_type, 'data': serializer.data})
        if BENCHMARK:
            # pp(queryset.explain(verbose=True, analyze=True))
            pp(connection.queries)
            queries_time = sum([float(s["time"]) for s in connection.queries])
            print(
                f"Queries total execution time: {queries_time} Num queries: {len(connection.queries)}"
            )
            reset_queries()

        queryset = list(chain(units_qs, services_qs, service_nodes_qs))
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(serializer.data)


"""
NOTES!!!

# Issues, questions to solve:
*  ":*"  to SearchQuery, django equalent for the sql statement: 
i.e. Unit.objects.filter(name__search="mus:*") does not work
One option, override SearchQuery class and it as_sql function?
site-packages/django/contrib/postgres/search.py

* munigeo and street search
* If service found, include units that has it as service???
* Order of services and howto include to queryset
# SearchVector
The SearchVector class constructs a stemmed, 
stopword-removed representation of the body column 
ready to be searched. The resulting queryset contains 
entries that are a match for “django”.
weights:
0.1, 0.2, 0.4, and 1.0,
D, C,B and A 

# Gindexes
Is added as column called search_column (as their content is generated by to_tsvector function)
to Unit, Serivce and ServiceNode models.
View
A view called SearchView that Unions searchable fields is then created and used when searching.
Currently a management script generates to content of the vector_columns, to be done with signals

# Query to find most common words
select * from ts_stat('SELECT search_column FROM search_view', 'ab') 
order by nentry desc, ndoc desc;

# To get supported languages:
SELECT cfgname FROM pg_ts_config;
tokens of normalized lexems. and the index 

# Debug search_query:
SELECT * FROM ts_debug('finnish', 'iso kissa istui ja söi rotan joka oli jo poissa');
Depending on the language settings the lexems are different.

  ## SQL search_query for suggestions
        # Note select * from services_unit where name @@ (to_tsquery('tur:*')) = true;
        #Manager.raw() Crashes if model has GIS fields see https://code.djangoproject.com/ticket/28632
        # Bug should be fixed, but seems to crash....
        #res = Unit.objects.raw("select * from services_unit")
        #res = Service.objects.raw("select * from services_unit where name @@ (to_tsquery('tur:*')) = true")




"""
