

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchHeadline
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.conf import settings
from django.db import connection
from django.db import connection, reset_queries
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from services.api import LANGUAGES
from services.models import ( 
    Service,
    ServiceNode,
    SearchView,
    Unit,  
    
)
from services.api import UnitSerializer
from pprint import pprint as pp
from collections import namedtuple


LANGUAGES={
    "en": "english",
    "fi": "finnish",
    "sv": "swedish"
}

class SuggestionSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    type = serializers.CharField()
    name = serializers.CharField()
        

def dictfetchall2(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def build_dict(cursor):
    results = []
    for row in cursor.fetchall():
        elem = {}
        elem["id"] = row[0].split("_")[1]
        elem["type"] = row[1]
        elem["name"] = row[2] 
        results.append(elem)
    return results


class SearchViewSet(APIView):

    def get(self, request):
        input_val = self.request.query_params.get("input", "").strip()
        q_val = self.request.query_params.get("q", "").strip()

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
        print(language)
        ## Find stop words
        print(input_val)
        
        ## SQL query for suggestions
        # Note select * from services_unit where name @@ (to_tsquery('tur:*')) = true;
        #Manager.rw() Crashes if model has GIS fields see https://code.djangoproject.com/ticket/28632
        # Bug should be fixed, but seems to crash....
        #res = Unit.objects.raw("select * from services_unit")
        #res = Service.objects.raw("select * from services_unit where name @@ (to_tsquery('tur:*')) = true")
        units_qs = None
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
            SELECT id, type_name, name_{language_short}, ts_rank_cd(vector_column, query)  AS rank
             FROM search_view, to_tsquery('{language}','^{input_val}:*') query
             WHERE query @@ vector_column ORDER BY rank DESC LIMIT 10;
             """           
       

            cursor.execute(sql)         
            results = build_dict(cursor)
            # NOTE, commented, now uses the SuggestionSerializer
            # unit_ids = []
            # service_ids = []
            # for e in results:
            #     if e["type"] == "Unit":
            #         unit_ids.append(e["id"].replace("unit_","")) 
            #     elif e["type"] == "Service":
            #         service_ids.append(e["id"].replace("service_","")) 
            #     elif e["type"] == "ServiceNode":
            #         service_ids.append(e["id"].replace("servicenode_","")) 

 

            # services = Service.objects.filter(id__in=service_ids)
            # units_qs = Unit.objects.filter(id__in=unit_ids)
            # units_qs = units_qs.union(Unit.objects.filter(services__in=service_ids))

            pp(connection.queries)
            print(results)
            print("Len dict: ", len(results))
            serializer = SuggestionSerializer(results, many=True)
            queries_time = sum([float(s["time"]) for s in connection.queries])
            print(f"Queries execution time: {queries_time} Num queries: {len(connection.queries)}")
      
            return Response(serializer.data)
         
            
        else:
            query = SearchQuery(q_val, config=language, search_type=search_type)
        
            # Search the Gindex
            # search_vector = SearchVector("vector_column", weight="A", config=language)  
            # # Search for columns thar not in the Gindex    
            # search_vector += SearchVector("extra", weight="B", config=language)
            # search_vector += SearchVector(f"services__name_"+language_short, weight="A", config=language)      
           
            # queryset = Unit.objects.annotate(rank=SearchRank(search_vector,query)).\
            #     filter(rank__gte=0.1).distinct().order_by("-rank")
            
           
            ## Search using VIEW!
            search_vector = SearchVector("vector_column", weight="A", config=language)   

            # queryset = SearchView.objects.annotate(rank=SearchRank(search_vector,query)).\
            #     filter(rank__gte=0.1).distinct().order_by("-rank")
            

            queryset = SearchView.objects.filter(vector_column=query)
            res_services = queryset.filter(type_name="Service")
            services_ids = [s.id.replace("service_","") for s in res_services]
            res_units = queryset.filter(type_name="Unit")
            units_ids = [s.id.replace("unit_","") for s in res_units]

            units_qs = Unit.objects.filter(id__in=units_ids)
            units_qs = units_qs.union(Unit.objects.filter(services__in=services_ids))

            servicenodes = queryset.filter(type_name="ServiceNode")
            
            #streets = queryset.filter(type_name="MunigeoStreet")


            # search_headline = SearchHeadline("name", query)
            # queryset = Unit.objects.annotate(search=query, rank=SearchRank(search_vector,query)) \
            #     .annotate(headline=search_headline).filter(search=query, rank__gte=0.1).order_by("-rank")     
             
            pp(queryset.explain(verbose=True, analyze=True))
            pp(connection.queries)
           
            print("QS Len;",len(queryset)) 
            #print(units_qs)
            print("Units Len;",len(units_qs))
            ser = UnitSerializer(units_qs, many=True)
            ## Bencmark output
            queries_time = sum([float(s["time"]) for s in connection.queries])
            print(f"Queries execution time: {queries_time} Num queries: {len(connection.queries)}")
            reset_queries()
            return Response(ser.data)
            
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



Synonmy list?


"""