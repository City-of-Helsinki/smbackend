from itertools import chain

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchHeadline
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.query_utils import Q
from django.conf import settings
from django.db import connection
from django.db import connection, reset_queries
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import serializers
from services.api_pagination import Pagination

from services.api import ServiceSerializer, UnitSerializer,  ServiceNodeSerializer
from services.models import ( 
    Service,
    ServiceNode,
    SearchView,
    Unit,  
    
)
from pprint import pprint as pp
from collections import namedtuple


LANGUAGES={
    "en": "english",
    "fi": "finnish",
    "sv": "swedish"
}

class SearchSerializer(serializers.Serializer):
    units = UnitSerializer(many=True)
    services = ServiceSerializer(many=True)
    service_nodes = ServiceNodeSerializer(many=True)
    
        
class SuggestionSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    type = serializers.CharField()
    name = serializers.CharField()
    location = serializers.SerializerMethodField(read_only=True)
    class Meta:
        fields = [
            "id",
            "type",
            "name",
            "location"
        ]
    
    def get_location(self, obj):
        if obj["type"] == "Unit":
            unit = Unit.objects.get(id=obj["id"])
            if unit.location:
                return unit.location.wkt
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


def get_ids_from_sql_results(all_results, type="Unit"):
    ids = []
    for row in all_results:
        if row[1] == type:
            # Id is the first col and in format 42_type.    
            ids.append(row[0].split("_")[1])
    return ids


class SearchViewSet(GenericAPIView):
    queryset = Unit.objects.all()
    def get_queryset(self):
        pass

    def get(self, request):

        SearchResult = namedtuple("SearchResult",("services", "units", "service_nodes"))
        input_val = self.request.query_params.get("input", "").strip()
        q_val = self.request.query_params.get("q", "").strip()
        types = self.request.query_params.get("type", "unit,service,service_node").split(",")

        language_short = self.request.query_params.get("lang", "fi").strip()
        language = LANGUAGES[language_short]
        """
        If search_type is 'plain', which is the default, the terms are treated as 
        separate keywords. If search_type is 'phrase', the terms are treated as a 
        single phrase. If search_type is 'raw', then you can provide a formatted search
         query with terms and operators. If search_type is 'websearch', then you can 
         provide a formatted search query, similar to the one used by web search engines. 'websearch' requires PostgreSQL ≥ 11. Read PostgreSQL’s Full Text Search docs to learn about differences and syntax. Examples:
        """
        search_type = "raw"             
          
        if input_val:       
            # Suggestions
            cursor = connection.cursor()
            sql = f"""
            SELECT services_unit.name, services_unit.id, services_unit.description, services_service.name
             FROM services_unit INNER JOIN services_service ON services_unit.id = services_service.id
             WHERE to_tsvector('finnish',services_unit.name || services_unit.description ||
              services_service.name) @@  (to_tsquery('finnish','{input_val}:*'));
             """
             # queryset = SearchView.objects.annotate(rank=SearchRank(search_vector,query)).\
            #     filter(rank__gte=0.1).distinct().order_by("-rank")
           
            sql = f"""
            SELECT id, type_name, name_{language_short}, ts_rank_cd(vector_column, query) AS rank
             FROM search_view, to_tsquery('{language}','^{input_val}:*') query
             WHERE query @@ vector_column ORDER BY rank DESC LIMIT 10;
             """           
       
            cursor.execute(sql)
            # Note fetchall 
            all_results = cursor.fetchall()        
            # results = build_dict(all_results)
       
            #serializer = SuggestionSerializer(results, many=True)
            # units_qs = Unit.objects.filter(id__in=get_ids_from_cursor(all_results, type="Unit"), public=True)
            # services_qs = Service.objects.filter(id__in=get_ids_from_cursor(all_results, type="Service"))
            # service_nodes_qs = ServiceNode.objects.filter(id__in=get_ids_from_cursor(all_results, type="ServiceNode"))
            unit_ids = get_ids_from_sql_results(all_results, type="Unit")
            service_ids = get_ids_from_sql_results(all_results, type="Service")
            service_node_ids = get_ids_from_sql_results(all_results, "ServiceNode")
        else:
            query = SearchQuery(q_val, config=language, search_type=search_type)             
            ## Search using VIEW!
            search_vector = SearchVector("vector_column", weight="A", config=language)   
            # NOTE, annotating with SearchRank slows(~100 times) the query, but results are the same.
            # queryset = SearchView.objects.annotate(rank=SearchRank(search_vector,query)).\
            #     filter(rank__gte=0.1).distinct().order_by("-rank")           

            queryset = SearchView.objects.filter(vector_column=query)
            
            # Services needs to be filtered even thou they are not serialized
            # Thus units that are in Services found in search need to be filtered.
            services = queryset.filter(type_name="Service")
            service_ids = [s.id.replace("service_","") for s in services]            
            units = queryset.filter(type_name="Unit")
            unit_ids = [u.id.replace("unit_","") for u in units]
            service_nodes = queryset.filter(type_name="ServiceNode")
            service_node_ids = [sn.id.replace("servicenode_","") for sn in service_nodes]
        
        if "service" in types:
            services_qs = Service.objects.filter(id__in=service_ids)
        else:
            services_qs = Service.objects.none()

        if "unit" in types:
            units_qs = Unit.objects.filter(id__in=unit_ids, public=True)
            units_qs = units_qs.union(Unit.objects.filter(services__in=service_ids, public=True))
        else:
            units_qs = Unit.objects.none()

        if "service_node" in types:  
            service_nodes_qs = ServiceNode.objects.filter(id__in=service_node_ids)
        else:
            service_nodes_qs = ServiceNode.objects.none()

        search_results = SearchResult(units=units_qs,
            services=services_qs, service_nodes=service_nodes_qs)
        serializer = SearchSerializer(search_results)
        
        ## Bencmark and print results
        #pp(queryset.explain(verbose=True, analyze=True))
        pp(connection.queries)        
        #print("QS Len;",len(queryset)) 
        #print(units_qs)
        #print("Units Len;",len(units_qs))
        
        queries_time = sum([float(s["time"]) for s in connection.queries])
        print(f"Queries execution time: {queries_time} Num queries: {len(connection.queries)}")
        reset_queries()
        
        queryset = list(chain(units_qs, services_qs, service_nodes_qs))
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(serializer.data)
            
"""
NOTES
Issues to solve:
*  ":*"  to SearchQuery, django equalent for the sql statement: 
i.e. Unit.objects.filter(name__search="mus:*") does not work

select * from services_unit where name @@ (to_tsquery('tur:*')) = true;
Which could be used to provide suggestions.

*  How the service of the Unit is added to the db.
*  Possible to inner join service_name to alter table sql state with generated columns

*  Possible to add the extra field to the vector_column as it is a json field
*  Find closest unit
*  Create good benchmarkin system.

* Aliases 
The SearchVector class constructs a stemmed, 
stopword-removed representation of the body column 
ready to be searched. The resulting queryset contains 
entries that are a match for “django”.
weights:
0.1, 0.2, 0.4, and 1.0,
D, C,B and A 

# Gind
Is added to the Unit model and then custom migration is migrated.
The custom migration uses generated columns that are supported on psql >=12.
No need to use trigger. But the migration needs to drop the column before altering.

# Query to find common words
select * from ts_stat('SELECT vector_column FROM services_unit', 'ab') 
order by nentry desc, ndoc desc;

# Suggestions: SearchRank, SearchHeadline ???
# To get supported languages:
SELECT cfgname FROM pg_ts_config;
tokens of normalized lexems. and the index

   ## SQL query for suggestions
        # Note select * from services_unit where name @@ (to_tsquery('tur:*')) = true;
        #Manager.raw() Crashes if model has GIS fields see https://code.djangoproject.com/ticket/28632
        # Bug should be fixed, but seems to crash....
        #res = Unit.objects.raw("select * from services_unit")
        #res = Service.objects.raw("select * from services_unit where name @@ (to_tsquery('tur:*')) = true")


Synonmy list?


"""