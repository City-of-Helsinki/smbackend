from itertools import chain
import re
from collections import namedtuple
from distutils.util import strtobool
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from django.contrib.gis.gdal import SpatialReference
from django.db.models import Case, When, Subquery
from django.db.models.query_utils import Q
from django.conf import settings
from django.db import connection, reset_queries
from django.db.models import Count
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import ParseError
from rest_framework import serializers
from munigeo import api as munigeo_api
from munigeo.api import AddressSerializer, AdministrativeDivisionSerializer
from munigeo.models import Address, AdministrativeDivision
from services.api import (
    ServiceSerializer,
    UnitSerializer,
    ServiceNodeSerializer,
    TranslatedModelSerializer,
)
from services.models import (
    Service,
    ServiceNode,
    SearchView,
    Unit,
)
from pprint import pprint as pp

BENCHMARK = True
LANGUAGES = {k: v.lower() for k, v in settings.LANGUAGES}
DEFAULT_SRS = SpatialReference(settings.DEFAULT_SRID)
SEARCHABLE_MODEL_TYPE_NAMES = ("Unit", "Service", "ServiceNode", "AdministrativeDivision", "Address")
QUERY_PARAM_TYPE_NAMES = [m.lower() for m in SEARCHABLE_MODEL_TYPE_NAMES]
#Note, default limit should be big enough, otherwise quality of results will drop..
DEFAULT_MODEL_LIMIT_VALUE = 20
# The limit value for the search query that search the search_view.
DEFAULT_SEARCH_SQL_LIMIT_VALUE = DEFAULT_MODEL_LIMIT_VALUE*5
# Todo refactor if possible 
class SearchResultBaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "name"]
        abstract = True


class SearchResultUnitSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Unit
        fields = ["id", "name", "provider_type"]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        if obj.location:
            representation["location"] = munigeo_api.geom_to_json(
                obj.location, DEFAULT_SRS
            )
        representation["num_services"] = obj.num_services
        return representation


class SearchResultServiceSerializer(
    TranslatedModelSerializer, serializers.ModelSerializer
):
    class Meta:
        model = Service
        fields = ["id", "name"]

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["units_count"] = obj.units__count
        return representation

class SearchResultAdministrativeDivisionSerializer(TranslatedModelSerializer, serializers.ModelSerializer):
    class Meta:
        model = AdministrativeDivision
        fields = ["id", "name"]


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


class SearchSerializer(serializers.Serializer):
    # addresses = AddressSerializer(many=True)
    # administrative_divisions = AdministrativeDivisionSerializer(many=True)
    # units = UnitSerializer(many=True)
    # services = ServiceSerializer(many=True)
    # service_nodes = ServiceNodeSerializer(many=True)
    units = SearchResultUnitSerializer(many=True)
    services = SearchResultServiceSerializer(many=True)
    addresses = SearchResultAddressSerializer(many=True)
    administrative_divisions = SearchResultAdministrativeDivisionSerializer(many=True)
    service_nodes = SearchResultServiceNodeSerializer(many=True)
 

class SearchSerializerChain(serializers.Serializer):
    @classmethod
    def get_serializer(cls, model):
        if model == Unit:
            return UnitSerializer
        elif model == Service:
            return ServiceSerializer
        elif model == ServiceNode:
            return ServiceNodeSerializer

    def to_representation(self, instance):
        serializer = self.get_serializer(instance.__class__)

        return serializer(instance, context=self.context).data


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

def get_all_ids_from_sql_results(all_results):
    ids = {}
    for t in SEARCHABLE_MODEL_TYPE_NAMES:
        ids[t] = []
    for row in all_results:
        ids[row[1]].append(row[0].split("_")[1])      
    return ids

def get_preserved_order(ids):    
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
    preserved = get_preserved_order(ids)
    if ids:
        return model.objects.filter(id__in=ids).order_by(preserved)
    else:
        return model.objects.none()


class SearchViewSet(GenericAPIView):
    queryset = Unit.objects.all()

    def get(self, request):
        sql_search = True
        model_limits = {}
        for model in list(QUERY_PARAM_TYPE_NAMES):
            model_limits[model] = DEFAULT_MODEL_LIMIT_VALUE     
        SearchResult = namedtuple(
            "SearchResult",
            (               
                "services",
                "units",
                "service_nodes",
                "administrative_divisions",
                "addresses",
            ),
        )

        params = self.request.query_params
        q_val = params.get("q", "").strip()
        if "sql" in params:
            try:
                sql_search = strtobool(params["sql"])
            except ValueError:
                raise ParseError("'sql' needs to be a boolean")
        # if "trigram" in params:
        #     try:
        #         trigram_search = strtobool(params["trigram"])
        #     except ValueError:
        #         raise ParseError("'trigram' needs to be a boolean")

        if not q_val:
            raise ParseError("Supply search terms with 'q=' '")

        types_str = ",".join([elem for elem in QUERY_PARAM_TYPE_NAMES])
        types = params.get(
            "type", types_str
        ).split(",")
        
        # Limit number of results
        if "limit" in params:
            try:
                search_sql_limit = int(params.get("limit"))
            except ValueError:
                raise ParseError("'limit' need to be of type integer.")
        else:
            search_sql_limit = DEFAULT_SEARCH_SQL_LIMIT_VALUE
        # read values for limits for each model
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
        search_type = "plain"
        search_query_str = None  # Used in the raw sql
        search_query = None  # Used with djangos filter
        # Build conditional searchquery.    
        q_vals = re.split(",\s+|\s+", q_val)
        for q in q_vals:

            if sql_search:
                if search_query_str:
                    # If word ends with "+"  make it or(|),
                    if q[-1] == "|":
                        search_query_str += f"| {q[:-1]}:*"
                    else:

                        search_query_str += f"& {q}:*"
                else:
                    search_query_str = f"{q}:*"
            else:
                if search_query:
                    if q[-1] == "+":
                        search_query |= SearchQuery(
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
            WHERE search_query @@ search_column 
            ORDER BY rank DESC LIMIT {search_sql_limit * len(QUERY_PARAM_TYPE_NAMES)};
            """
            cursor = connection.cursor()
            cursor.execute(sql)
            # Note fetchall() consumes the results and once called returns None.
            all_results = cursor.fetchall()
            all_ids = get_all_ids_from_sql_results(all_results)            
            unit_ids = all_ids["Unit"]
            service_ids = all_ids["Service"]
            service_node_ids = all_ids["ServiceNode"]            
            administrative_division_ids = all_ids["AdministrativeDivision"]           
            address_ids = all_ids["Address"]

        else:
            # NOTE, Using djangos search is ~100 times slower than raw sql
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
            for elem in queryset.all()[:search_sql_limit]:
                if elem.type_name == "Service":
                    service_ids.append(elem.id.replace("service_", ""))
                elif elem.type_name == "Unit":
                    unit_ids.append(elem.id.replace("unit_", ""))
                elif elem.type_name == "ServiceNode":
                    service_node_ids.append(elem.id.replace("servicenode_", ""))
                elif elem.type_name == "Address":
                    service_node_ids.append(elem.id.replace("address_", ""))
                elif elem.type_name == "AdministrativeDivision":
                    service_node_ids.append(elem.id.replace("administrativedivision_", ""))

        if "service" in types:
            preserved = get_preserved_order(service_ids)
            services_qs = Service.objects.filter(id__in=service_ids).order_by(preserved)
            if not services_qs:
                services_qs = get_trigram_results(
                    Service, "name_" + language_short, q_val
                )             
            services_qs = services_qs.all().distinct()
            services_qs = services_qs.annotate(Count("units")).order_by("-units__count")
            services_qs = services_qs[:model_limits["service"]]

        else:
            services_qs = Service.objects.none()

        if "unit" in types:            
            preserved = get_preserved_order(unit_ids)
            # if preserved:
            units_qs = Unit.objects.filter(id__in=unit_ids).order_by(preserved)
            units_from_services = Unit.objects.filter(
                services__in=service_ids, public=True
            )
            # Add units which are associated with the services found.
            units_qs = units_from_services | units_qs
            ids1 = list(units_from_services.values_list("id", flat=True))
            ids2 = list(units_qs.values_list("id", flat=True))
            ids1 = []
            ids = ids1 + ids2
            units_qs = Unit.objects.filter(id__in=ids)

            #if trigram_search:  # or not units_qs:
            if not units_qs:
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

            units_qs = units_qs.annotate(num_services=Count("services")).order_by("provider_type","-num_services")
            units_qs = units_qs[:model_limits["unit"]]
        else:
            units_qs = Unit.objects.none()

        # if "servicenode" in types:
        #     service_nodes_qs = ServiceNode.objects.filter(id__in=service_node_ids)[:model_limits["servicenode"]]
        # else:
        #TODO ? remove all service_node related stuff from migrations, models etc...
        service_nodes_qs = ServiceNode.objects.none()
        if "administrativedivision" in types:
            administrative_division_qs = AdministrativeDivision.objects.filter(
                id__in=administrative_division_ids
            )
            if not administrative_division_qs:
                administrative_division_qs = get_trigram_results(AdministrativeDivision, "name_" + language_short, q_val)
        
            administrative_division_qs = administrative_division_qs[:model_limits["administrativedivision"]]
        else:
            administrative_division_qs = AdministrativeDivision.objects.none()

        if "address" in types:
            address_qs = Address.objects.filter(id__in=address_ids)
            if not address_qs:
                address_qs = get_trigram_results(Address, "full_name_" + language_short, q_val)
            address_qs = address_qs[:model_limits["address"]]
        else:
            address_qs = Address.objects.none()
      
        search_results = SearchResult(
            units=units_qs,
            services=services_qs,
            service_nodes=service_nodes_qs,
            administrative_divisions=administrative_division_qs,
            addresses=address_qs,
        )
        serializer = SearchSerializer(search_results)
            
        if BENCHMARK:
            # pp(queryset.explain(verbose=True, analyze=True))
            pp(connection.queries)
            queries_time = sum([float(s["time"]) for s in connection.queries])
            print(
                f"Queries total execution time: {queries_time} Num queries: {len(connection.queries)}"
            )
            reset_queries()

        queryset = list(
            chain(
                units_qs,
                services_qs,
                service_nodes_qs,
                administrative_division_qs,
                address_qs,
            )
        )  

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
