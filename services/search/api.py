import json
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchHeadline
from django.contrib.postgres.search import TrigramSimilarity
from django.http import HttpResponse
from django.db import connection, reset_queries
from rest_framework.views import APIView
from rest_framework.response import Response
from services.api import LANGUAGES
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
from pprint import pprint as pp

LANGUAGES={
    "en": "english",
    "fi": "finnish",
    "sv": "swedish"
}
class SearchViewSet(APIView):

    def get(self, request):
        input_val = self.request.query_params.get("input", "").strip()
        input_lang = self.request.query_params.get("lang", "fi").strip()
        language = LANGUAGES[input_lang]
        """
        If search_type is 'plain', which is the default, the terms are treated as 
        separate keywords. If search_type is 'phrase', the terms are treated as a 
        single phrase. If search_type is 'raw', then you can provide a formatted search
         query with terms and operators. If search_type is 'websearch', then you can 
         provide a formatted search query, similar to the one used by web search engines. 'websearch' requires PostgreSQL ≥ 11. Read PostgreSQL’s Full Text Search docs to learn about differences and syntax. Examples:
        """
        search_type = "websearch"
        print(language)
        ## SQL query for suggestions
        # Note select * from services_unit where name @@ (to_tsquery('tur:*')) = true;
       
        # Search the Gindex
        search_vector = SearchVector("vector_column", weight="A", config=language)
        # Search for columns thar not in the Gindex
        # TODO, service__name hits to many units in some searches.e.g. "steiner"
        search_vector += SearchVector(f"services__name_"+input_lang, weight="B", config=language)
        search_vector += SearchVector("extra", weight="B", config=language)
             
        query = SearchQuery(input_val, config=language, search_type=search_type)
        queryset = Unit.objects.annotate(rank=SearchRank(search_vector,query)).\
            filter(rank__gte=0.1).order_by("-rank")

        # search_headline = SearchHeadline("name", query)
        # queryset = Unit.objects.annotate(search=query, rank=SearchRank(search_vector,query)) \
        #     .annotate(headline=search_headline).filter(search=query, rank__gte=0.1).order_by("-rank")


        
  
        ## Bencmark output
        print(input_val)
        pp(connection.queries)
        print(Unit.objects.annotate(rank=SearchRank(search_vector,query)).\
            filter(rank__gte=0.1).order_by("-rank").explain(verbose=True, analyze=True))
        reset_queries()
        print(queryset)
        breakpoint()
        json_res = []
        for q in queryset:
            json_obj = dict(name=q.name)
            json_res.append(json_obj)
        return HttpResponse(str(len(queryset))+json.dumps(json_res))
        
"""
NOTES
Issues to solve:
*  ":*"  to SearchQuery, django equalent for the sql statement: 
select * from services_unit where name @@ (to_tsquery('tur:*')) = true;
Which could be used to provide suggestions.

*  How the service of the Unit is added to the db.
*  Possible to inner join service_name to alter table sql state with generated columns

*  Possible to add the extra field to the vector_column as it is a json field
*  Find closest unit
*  Creaate good benchmarkin system.
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

# Suggestions: SearchRank, SearchHeadline ???
# To get supported languages:
SELECT cfgname FROM pg_ts_config;
tokens of normalized lexems. and the index


"""