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
    "query": {
        "filtered": {
            "query": {
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": "suggest",
                                "inner_hits": {
                                    "_source": false,
                                    "highlight": {
                                        "order": "score",
                                        "pre_tags": ["{"],
                                        "post_tags": ["}"],
                                        "fields": {
                                            "suggest.name": {"number_of_fragments": 10},
                                            "suggest.location": {"number_of_fragments": 10},
                                            "suggest.service": {"number_of_fragments": 10}
                                        }
                                    }
                                },
                                "query": {
                                    "bool": {
                                        "should": [
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "nested": {
                                "path": "partial",
                                "inner_hits": {
                                    "_source": false,
                                    "highlight": {
                                        "order": "score",
                                        "pre_tags": ["{"],
                                        "post_tags": ["}"],
                                        "fields": {
                                            "partial.name": {"number_of_fragments": 10},
                                            "partial.location": {"number_of_fragments": 10},
                                            "partial.service": {"number_of_fragments": 10}
                                        }
                                    }
                                },
                                "query": {
                                    "bool": {
                                        "should": [
                                        ]
                                    }
                                }
                            }
                        }
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
                        "or": [
                            {
                                "query": {
                                    "match": {
                                        "text": "insert and text and here"
                                    }
                                }
                            },
                            {
                                "query": {
                                    "match": {
                                        "text": "insert text without last word here"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }
}
"""


def unit_count(search_query):
    data = requests.get('http://localhost:8000/v2/search/?type=unit&q={}'.format(search_query)).json()
    return data['count']


def get_suggestions(search_query, elastic_query=False):
    query_parts = search_query.split()
    query_complete_part = " ".join(query_parts[:-1])
    query_incomplete_part = query_parts[-1]

    query = json.loads(BASE_QUERY)

    if len(search_query.strip()) == 0:
        return None

    partial_query = [
        {'match': {'partial.name': {'query': query_incomplete_part}}},
        {'match': {'partial.location': {'query': query_incomplete_part}}},
        {'match': {'partial.service': {'query': query_incomplete_part}}}
    ]

    if len(query_parts) == 1:
        query['query']['filtered']['query']['bool']['should'][0]['nested']['query']['bool']['should'] = [
            {'match': {'suggest.name': {'query': search_query, 'operator': 'and'}}},
            {'match': {'suggest.location': {'query': search_query, 'operator': 'and'}}},
            {'match': {'suggest.service': {'query': search_query, 'operator': 'and'}}}
        ]
        query['query']['filtered']['query']['bool']['should'][1]['nested']['query']['bool']['should'] = partial_query
    elif len(query_parts) > 1:
        query['query']['filtered']['query']['bool']['should'][0]['nested']['query']['bool']['should'] = [
            {'match': {'suggest.name': {'query': query_complete_part, 'operator': 'and'}}},
            {'match': {'suggest.location': {'query': query_complete_part, 'operator': 'and'}}},
            {'match': {'suggest.service': {'query': query_complete_part, 'operator': 'and'}}},
            {'match': {'suggest.name': {'query': query_incomplete_part, 'operator': 'and'}}},
            {'match': {'suggest.location': {'query': query_incomplete_part, 'operator': 'and'}}},
            {'match': {'suggest.service': {'query': query_incomplete_part, 'operator': 'and'}}}
        ]
        query['query']['filtered']['query']['bool']['should'][1]['nested']['query']['bool']['should'] = partial_query

    if len(query_parts) > 1:
        query['query']['filtered']['filter']['and'][1]['or'][0]['query']['match']['text'] = {
            "query": "{}".format(" ".join(query_parts)),
            "operator": "and"
        }
        query['query']['filtered']['filter']['and'][1]['or'][1]['query']['match']['text'] = {
            "query": "{}".format(query_complete_part),
            "operator": "and"
        }
    else:
        del query['query']['filtered']['filter']['and'][1]

    if elastic_query:
        return json.dumps(query, indent=2)

    response = requests.get(
        '{}/_search'.format(ELASTIC),
        data=json.dumps(query))
    result = response.json()
    # import pprint
    # pprint.pprint(result)

    suggestions_complete = dict()    # already matched fields
    suggestions_incomplete = dict()  # partially matching fields
    next_steps = dict()              # for units in this set, what filters to add next?

    for doc in result.get('hits', {}).get('hits', []):
        # TODO REFACTOR BELOW
        for partial in doc['inner_hits']['partial']['hits']['hits']:
            for suggestion_type, highlights in partial['highlight'].items():
                suggestions_incomplete.setdefault(suggestion_type, {})
                for highlight in highlights:
                    count = suggestions_incomplete[suggestion_type].get(highlight, 0)
                    suggestions_incomplete[suggestion_type][highlight] = count + 1
        for complete in doc['inner_hits'].get('suggest', {}).get('hits', {}).get('hits', []):
            for suggestion_type, highlights in complete['highlight'].items():
                suggestions_complete.setdefault(suggestion_type, {})
                for highlight in highlights:
                    count = suggestions_complete[suggestion_type].get(highlight, 0)
                    suggestions_complete[suggestion_type][highlight] = count + 1
        for suggestion_type, next_suggestions in doc['_source']['suggest'].items():
            next_steps.setdefault(suggestion_type, {})
            if isinstance(next_suggestions, str):
                next_suggestions = [next_suggestions]
            for next_suggestion in next_suggestions:
                count = next_steps[suggestion_type].get(next_suggestion, 0)
                next_steps[suggestion_type][next_suggestion] = count + 1

    # todo: remove already "used" suggestions (existing in query)

    return {'complete': suggestions_complete,
            'incomplete': suggestions_incomplete,
            'next': next_steps}


def suggestion_query(query):
    print(get_suggestions(query, elastic_query=True))
    return None


def p(val):
    if val:
        pprint(val)


FUNC = get_suggestions
# FUNC = suggestion_query

if False:
    p(FUNC("saksan wlan ala-aste"))
    p(FUNC("helsinki uimastadion maa"))
    p(FUNC("uimastadion"))
    p(FUNC("ranska"))
    p(FUNC("ranska esiope"))
    p(FUNC("A1-ranska esiopetus (koulun järjestämä)"))
    p(FUNC("A1-ranska esiopetus (koulun järjestämä) normaalikoulu"))
    p(FUNC("ui"))

    # FUN: note the difference in analysis:
    p(FUNC("helsing"))
    p(FUNC("helsink"))
    p(FUNC("helsingin"))

# TODO: problem 1: actual services come below
