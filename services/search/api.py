from itertools import chain
from collections import namedtuple
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.query_utils import Q
from django.conf import settings
from django.db import connection, reset_queries
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import ParseError
from rest_framework import serializers

from services.api import ServiceSerializer, UnitSerializer,  ServiceNodeSerializer
from services.models import ( 
    Service,
    ServiceNode,
    SearchView,
    Unit,  
    
)
from pprint import pprint as pp

LANGUAGES = {k:v.lower() for k,v in settings.LANGUAGES}

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

        if not input_val and not q_val:
            raise ParseError(
                "Supply search terms with 'q=' or autocomplete entry with 'input='"
            )
        if input_val and q_val:
            raise ParseError("Supply either 'q' or 'input', not both")


        types = self.request.query_params.get("type", "unit,service,service_node").split(",")
        # Limit number os "suggestions"
        limit = self.request.query_params.get("limit", 10)
        language_short = self.request.query_params.get("lang", "fi").strip()
        language = LANGUAGES[language_short]
        print(language*10)
        """

        If search_type is 'plain', which is the default, the terms are treated as 
        separate keywords. If search_type is 'phrase', the terms are treated as a 
        single phrase. If search_type is 'raw', then you can provide a formatted search
         search_query with terms and operators. If search_type is 'websearch', then you can 
         provide a formatted search search_query, similar to the one used by web search engines. 'websearch' requires PostgreSQL ≥ 11. Read PostgreSQL’s Full Text Search docs to learn about differences and syntax. Examples:
        """
        search_type = "phrase"             
          
        if input_val:       
            # "Suggestions"
            cursor = connection.cursor()
           # queryset = SearchView.objects.annotate(rank=SearchRank(search_vector,search_query)).\
            #     filter(rank__gte=0.1).distinct().order_by("-rank")
           
            sql = f"""
            SELECT id, type_name, name_{language_short}, ts_rank_cd(vector_column, search_query) AS rank
             FROM search_view, to_tsquery('{language}','^{input_val}:*') search_query
             WHERE search_query @@ vector_column ORDER BY rank DESC LIMIT {limit};
             """           
       
            cursor.execute(sql)
            # Note fetchall() consumes the results and once called returns None. 
            all_results = cursor.fetchall()        
            # results = build_dict(all_results)
       
            #serializer = SuggestionSerializer(results, many=True)
        
            unit_ids = get_ids_from_sql_results(all_results, type="Unit")
            service_ids = get_ids_from_sql_results(all_results, type="Service")
            service_node_ids = get_ids_from_sql_results(all_results, "ServiceNode")
        else:
            #search_query = SearchQuery(q_val, config=language, search_type=search_type)             
        
            q_vals = q_val.split(",")            
            search_query = SearchQuery(q_vals[0], config=language, search_type=search_type)             
            # Add conditional searchquerys. 
            if len(q_vals)>1:
                for i in range(1, len(q_vals)):  
                    q = q_vals[i] 
                    #If word end whit "."  make it a and, i.e. must be included.
                    if q[-1] == ".":
                        search_query &= SearchQuery(q, config=language, search_type=search_type) 
                    else:
                        search_query |= SearchQuery(q, config=language, search_type=search_type) 
            
            ## Search using VIEW!
            #search_vector = SearchVector("vector_column", weight="A", config=language)   
            # NOTE, annotating with SearchRank slows(~100 times) the search_query, but results are the same.
            # queryset = SearchView.objects.annotate(rank=SearchRank(search_vector,search_query)).\
            #     filter(rank__gte=0.1).distinct().order_by("-rank")           
            queryset = SearchView.objects.filter(vector_column=search_query)
            #queryset = SearchView.objects.annotate(similarity=TrigramSimilarity("vector_column", "turku"),).filter(similarity__gt=0.3).order_by('-similarity')

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
            #municipalities = ["kaarina", "salo", "raisio"]
            units_qs = Unit.objects.filter(id__in=unit_ids, public=True)
            # Add Units that are in services found in search.
            units_from_services = Unit.objects.filter(services__in=service_ids, public=True)
            units_qs = units_qs | units_from_services

            if "municipality" in self.request.query_params:
                municipalities = self.request.query_params["municipality"].lower().strip().split(",")
                if municipalities[0] != "":                    
                    units_qs = units_qs.filter(municipality_id__in=municipalities)
            if "service" in self.request.query_params:
                services = self.request.query_params["service"].strip().split(",")
                if services[0] != "":
                    units_qs = units_qs.filter(services__in=services)                
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
        print(f"Queries total execution time: {queries_time} Num queries: {len(connection.queries)}")
        reset_queries()
        
        queryset = list(chain(units_qs, services_qs, service_nodes_qs))
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(serializer.data)
            
"""
NOTES
# Issues to solve:
*  ":*"  to SearchQuery, django equalent for the sql statement: 
i.e. Unit.objects.filter(name__search="mus:*") does not work
*  Find closest unit
*  Create good benchmarkin system.
* munigeo and street search



# SearchVector
The SearchVector class constructs a stemmed, 
stopword-removed representation of the body column 
ready to be searched. The resulting queryset contains 
entries that are a match for “django”.
weights:
0.1, 0.2, 0.4, and 1.0,
D, C,B and A 

# Gindexes
Is added as column called vector_column (as their content is generated by to_tsvector function)
to Unit, Serivce and ServiceNode models.
View
A view called SearchView that Unions searchable fields is then created and used when searching.
Currently a management script generates to content of the vector_columns, to be done with signals

# Query to find most common words

select * from ts_stat('SELECT vector_column FROM search_view', 'ab') 
order by nentry desc, ndoc desc;

# To get supported languages:
SELECT cfgname FROM pg_ts_config;
tokens of normalized lexems. and the index

 

# Debug search_query:
SELECT * FROM ts_debug('english', 'iso kissa istui ja söi rotan joka oli jo poissa');
Depending on the settings the lexems are different.


  ## SQL search_query for suggestions
        # Note select * from services_unit where name @@ (to_tsquery('tur:*')) = true;
        #Manager.raw() Crashes if model has GIS fields see https://code.djangoproject.com/ticket/28632
        # Bug should be fixed, but seems to crash....
        #res = Unit.objects.raw("select * from services_unit")
        #res = Service.objects.raw("select * from services_unit where name @@ (to_tsquery('tur:*')) = true")




"""