import requests
import json
from pprint import pprint
from collections import OrderedDict


class OrderedByScoreDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        self.max_score = 0
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        score = value['score']
        if score > self.max_score:
            self.move_to_end(key, last=False)
            self.max_score = score


ELASTIC = 'http://localhost:9200/servicemap-fi/'
BASE_QUERY = """
{
  "_source": ["suggest"],
  "size": 200,
  "highlight": {
    "fields": {
      "suggest": {},
      "suggest.part": {}
    }
  },
  "aggs" : {
    "name" : {
      "terms" : { "field" : "suggest.name.raw", "size": 5, "order": {"avg_score": "desc"} },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "location" : {
      "terms" : { "field" : "suggest.location.raw", "size": 10, "order": {"avg_score": "desc"}  },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "service" : {
      "terms" : { "field" : "suggest.service.raw", "size": 100, "order": {"avg_score": "desc"}   },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "complete_matches" : {
      "filter" : {
        "query": {
          "query_string": {
            "default_field":"text",
            "default_operator": "AND",
            "query": "(text:() OR extra_searchwords:())"
          }
        }
      }
    }
  },
  "query": {
    "filtered": {
      "query": {
        "bool": {
          "should": [
          ]
        }
      },
      "filter": {
        "and": [
          {
            "terms": {
              "django_ct": ["services.unit"]
            }
          },
          {
            "query": {
              "bool": {
                "must": [
                  {
                    "match": {
                      "text": {
                        "query": "insert and text and here",
                        "operator": "and"
                      }
                    }
                  },
                  {
                    "bool": {
                      "should": [
                        { "match": {"suggest.service": "text"}},
                        { "match": {"suggest.name": "text"}},
                        { "match": {"suggest.location": "text"}}
                      ]
                    }
                  }
                ]
              }
            }
          }
        ]
      }
    }
  }
}



"""


def unit_results(search_query):
    _next = 'http://localhost:8000/v2/search/?type=unit&q={}'.format(search_query)
    results = []
    while _next is not None:
        data = requests.get(_next).json()
        _next = data['next']
        results += data['results']
    return results


def _matches_complete_word_tokens(result):
    return result.get('aggregations', {}).get('complete_matches', {}).get('doc_count', 1) > 0


def get_suggestions(query):
    result = suggestion_response(query)

    last_word_probably_incomplete = _matches_complete_word_tokens(result)
    last_word = query.split()[-1]

    for _type, value in result['aggregations'].items():
        if _type == 'location' and len(value['buckets']) == 1 or _type == 'complete_matches':
            continue
        print("\n{}".format(_type))
        print("".join(("=" for x in range(0, len(_type)))))
        for term in value.get('buckets', []):
            text = term['key']
            if last_word.lower() in text.lower():
                text += "** "
            print(text, "[{}]".format(term['avg_score']['value']))
    # rule 1: remove buckets with only one possibility (redundant) DONE
    # rule 2: show most restrictive + least restrictive?
    #  (except can't differentiate between multiple most restrictives)
    # rule 3: if there are only one results, period, just show the name of the unit?


def suggestion_response(query):
    response = requests.get(
        '{}/_search/?search_type=count'.format(ELASTIC),
        data=json.dumps(suggestion_query(query)))
    return response.json()


def suggestion_query(search_query):
    search_query = search_query.strip()
    query = json.loads(BASE_QUERY)

    if len(search_query) == 0:
        return None

    last_word = None
    first_words = None
    split = search_query.split()
    if len(split) > 0:
        last_word = split[-1]
        first_words = " ".join(split[:-1])

    query['aggs']['complete_matches']['filter']['query']['query_string']['query'] = (
        "(text:({0}) OR extra_searchwords:({0}))".format(search_query))

    query['query']['filtered']['query']['bool']['should'] = [
        {'match': {'suggest.name': {'query': search_query}}},
        {'match': {'suggest.location': {'query': search_query}}},
        {'match': {'suggest.service': {'query': search_query}}}
    ]
    # del query['query']['filtered']['filter']['and'][1]
    filter_query_must = query['query']['filtered']['filter']['and'][1]['query']['bool']['must']

    if first_words:
        filter_query_must[0]['match']['text']['query'] = first_words
        filter_query_must[1]['bool']['should'][0]['match']['suggest.service'] = last_word
        filter_query_must[1]['bool']['should'][1]['match']['suggest.name'] = last_word
        filter_query_must[1]['bool']['should'][2]['match']['suggest.location'] = last_word
    else:
        del query['query']['filtered']['filter']['and'][1]
    return query


def p(val):
    if val:
        pprint(val, width=100)


def f(q):
    p(suggestion_query(q))
    p(suggestion_response(q))
    get_suggestions(q)


def loop():
    while True:
        q = input("\nsearch: ")
        if q == '' or q == '.':
            break
        elif q[-1] == '?':
            for r in unit_results(q[:-1]):
                print(r['name']['fi'], r['score'])
        else:
            f(q)


if False:
    # saksan wlan ala-aste
    # helsinki uimastadion maa
    # uimastadion
    # ranska
    # ranska esiope
    # A1-ranska esiopetus (koulun järjestämä)
    # A1-ranska esiopetus (koulun järjestämä) normaalikoulu
    # ui

    # # FUN: note the difference in analysis:
    # helsing
    # helsink
    # helsingin
    pass

