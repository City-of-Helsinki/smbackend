import requests
import json
from collections import OrderedDict
import re
import pprint


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
      "terms" : { "field" : "suggest.name.raw", "size": 30, "order": {"avg_score": "desc"} },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "location" : {
      "terms" : { "field" : "suggest.location.raw", "size": 10, "order": {"avg_score": "desc"}  },
      "aggs": { "avg_score": { "avg": {"script": "_score"}}}
    },
    "service" : {
      "terms" : { "field" : "suggest.service.raw", "size": 50, "order": {"avg_score": "desc"}   },
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


def generate_suggestions(query):
    query_lower = query.lower()
    result = suggestion_response(query)

    last_word = query.split()[-1]

    last_word_lower = last_word.lower()
    last_word_re = re.compile(last_word_lower + r'[-\w]*', flags=re.IGNORECASE)

    suggestions_by_type = {}
    completions = []
    minimal_completions = {}

    match_id = -1
    for _type, value in result['aggregations'].items():
        if _type == 'location' and len(value['buckets']) == 1 or _type == 'complete_matches':
            continue
        for term in value.get('buckets', []):
            text = term['key']
            text_lower = text.lower()
            match_type = 'indirect'
            boundaries = None
            full_match = query_lower.find(text_lower)
            if full_match == 0:
                boundaries = [0, len(text_lower)]
                match_type = 'full_query'
            else:
                partial_match = text_lower.find(last_word_lower)
                if partial_match != -1:
                    boundaries = [partial_match, partial_match + len(last_word_lower) + 1]
                    match_type = 'prefix'

            match_id += 1
            match = {
                'id': match_id,
                'text': text,
                'score': term['avg_score']['value'],
                'doc_count': term['doc_count'],
                'match': {
                    'type': _type,
                    'match_type': match_type,
                    'match_boundaries': boundaries
                }
            }
            if match_type == 'prefix':
                match_copy = match.copy()
                text = match_copy['text']
                match_copy['original'] = text
                matching_part = last_word_re.search(text)
                if matching_part:
                    match_copy['text'] = matching_part.group(0)
                    existing_completion = minimal_completions.get(match_copy['text'])
                    if existing_completion:
                        count = existing_completion['count']
                    else:
                        count = 0
                    match_copy['count'] = count + 1
                    minimal_completions[match_copy['text']] = match_copy
            if _type == 'name' and match_type == 'indirect':
                continue
            if _type == 'service' and match_type == 'full_query':
                continue
            if match_type == 'indirect':
                suggestions_by_type.setdefault(_type, []).append(match)
            else:
                completions.append(match)

    suggestions_by_type['completions'] = completions
    suggestions_by_type['minimal_completions'] = [v for v in minimal_completions.values() if v['count'] > 1]

    return {
        'query': query,
        'incomplete_query': not _matches_complete_word_tokens(result),
        'suggestions': suggestions_by_type
    }
    # rule 1: remove buckets with only one possibility (redundant) DONE
    # indire


ACTIVE_MATCH_TYPES = ['minimal_completions', 'completions', 'service', 'name', 'location']
LIMITS = {
    'minimal_completions': 10,
    'completions': 10,
    'service': 10,
    'name': 10,
    'location': 5}

# TODO eliminate arabiankielinen -> arabiankielinen päiväh


def output_suggestion(match, query):
    if match['match']['match_type'] == 'indirect':
        suggestion = '{} {}'.format(match['text'], query)
    else:
        suggestion = match['text']
    return {
        'suggestion': suggestion,
        'count': match.get('doc_count')
    }

# problem arabia päiväkoti islamilainen päiväkoti


def choose_suggestions(suggestions, limits=LIMITS):
    # rule 2: show most restrictive + least restrictive?
    #  (except can't differentiate between multiple most restrictives)
    # rule 3: if there are only one results, period, just show the name of the unit?
    #   no: show whatever matches best

    # TODO ! Must prefer "phrase prefix" matches: kallion kir -> kallion kirjasto/kirkko
    # to kauklahden kir -- this is reflected in the score currently, but must make better
    query = suggestions['query']
    if suggestions['incomplete_query']:
        active_match_types = ['minimal_completions', 'completions']
    else:
        active_match_types = ['completions', 'service', 'name', 'location']
    suggestions_by_type = suggestions['suggestions']
    # results_per_type = math.floor(limit / len(suggestions_by_type.keys()))
    results = [output_suggestion(match, query)
               for _type in active_match_types
               for match in suggestions_by_type.get(_type, [])[0:limits[_type]]]
    return {
        'suggestions': results,
        'requires_completion': suggestions['incomplete_query']
    }
    # ordering
    # 1. minimal completions with doc_count == 1
    #    ordered by score
    # 2. minimal completions with more docs
    #    ordered by score
    # 3. other remaining completions ordered by score ?
    # full queries: add locations (randomly?)
    # rule 1: remove buckets with only one possibility (redundant) DONE
    # rule 2: show most restrictive + least restrictive?
    #  (except can't differentiate between multiple most restrictives)
    # rule 3: if there are only one results, period, just show the name of the unit?

    #   NOTE: actually, the tarkennus won't show up in the ui for already single-matching queries


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


def get_suggestions(query):
    return choose_suggestions(generate_suggestions(query))


def p(val):
    if val:
        pprint.pprint(val, width=100)


def f(q):
    # p(suggestion_query(q))
    # p(suggestion_response(q))
    suggestions = generate_suggestions(q)
    pprint.pprint(suggestions)
    chosen_suggestions = choose_suggestions(suggestions)
    pprint.pprint(chosen_suggestions)
    for s in chosen_suggestions['suggestions']:
        print('{} ({} toimipistettä)'.format(s['suggestion'], s['count']))


def loop():
    while True:
        q = input("\nsearch: ")
        if q == '' or q == '.':
            break
        elif q[-1] == '?':
            results = unit_results(q[:-1])
            for r in results:
                print(r['name']['fi'],
                      'https://palvelukartta.hel.fi/unit/{}'.format(r['id']),
                      r['score'])
            print(len(results))
        else:
            f(q)
