import json
import logging
import pprint
import re
import string

import requests
from django.conf import settings
from rest_framework import status

logger = logging.getLogger(__name__)


LETTER_RE = re.compile("[{}]+".format(string.digits + re.escape(string.punctuation)))


def word_is_alphabetic(word):
    return not LETTER_RE.fullmatch(word)


def get_elastic(language):
    try:
        return next(
            (
                "{}{}/".format(c["URL"], c["INDEX_NAME"])
                for k, c in settings.HAYSTACK_CONNECTIONS.items()
                if k == "default-{}".format(language)
            )
        )
    except StopIteration:
        raise ValueError("Unconfigured language {}".format(language))


# TODO: refactor into smaller pieces.
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
      "terms" : { "field" : "suggest.name.raw", "size": 500, "order": {"max_score": "desc"} },
      "aggs": { "max_score": { "max": {"script": "_score"}},
                "tops": {"top_hits": {"size":1, "_source": {"include": ["name"]}}}}

    },
    "location" : {
      "terms" : { "field" : "suggest.location.raw", "size": 10},
      "aggs": { "max_score": { "max": {"script": "_score"}},
                "tops": {"top_hits": {"size":1, "_source": {"include": ["name"]}}}}
    },
    "keyword" : {
      "terms" : { "field" : "suggest.keyword.raw", "size": 10},
      "aggs": { "max_score": { "max": {"script": "_score"}},
                "tops": {"top_hits": {"size":1, "_source": {"include": ["name"]}}}}
    },
    "service" : {
      "terms" : { "field" : "suggest.service.raw", "size": 50},
      "aggs": { "max_score": { "max": {"script": "_score"}},
                "tops": {"top_hits": {"size":1, "_source": {"include": ["name"]}}}}
    },
    "complete_matches" : {
      "filter" : {
        "and": [
          {
            "query": {
              "query_string": {
                "default_field":"text",
                "default_operator": "AND",
                "query": "(text:() OR extra_searchwords:())"
              }
            }
          },
          {
            "terms": {
              "public": [true]
            }
          }
        ]
      }
    }
  },
  "query": {
    "filtered": {
      "query": { },
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
                        "query": "insert query here",
                        "operator": "and"
                      }
                    }
                  },
                  { }
                ]
              }
            }
          },
          {
            "terms": {
              "public": [true]
            }
          }
        ]
      }
    }
  }
}

"""


def unit_results(search_query):
    _next = "http://localhost:8000/v2/search/?type=unit&q={}".format(search_query)
    results = []
    while _next is not None:
        data = requests.get(_next).json()
        _next = data["next"]
        results += data["results"]
    return results


def _matches_complete_word_tokens(result):
    return (
        result.get("aggregations", {}).get("complete_matches", {}).get("doc_count", 1)
        > 0
    )


def generate_suggestions(query, language):
    query_lower = query.lower()
    result = suggestion_response(query, language)
    if "hits" in result and result["hits"]["total"] == 0 and len(query.split()) > 1:
        return None

    last_word = query.split()[-1]

    last_word_lower = last_word.lower()
    last_word_re = re.compile(
        re.escape(last_word_lower) + r"[-\w]*", flags=re.IGNORECASE
    )

    suggestions_by_type = {}
    minimal_completions = {}

    match_id = -1
    if "aggregations" in result:
        for _type, value in result["aggregations"].items():
            if (
                _type == "location"
                and len(value["buckets"]) == 1
                or _type == "complete_matches"
            ):
                continue
            for term in value.get("buckets", []):
                text = term["key"]
                text_lower = text.lower()
                match_type = "indirect"
                boundaries = None

                if text_lower.strip() == query_lower.strip():
                    match_type = "full_query_match"
                else:
                    full_match = query_lower.find(text_lower)
                    if full_match != -1:
                        boundaries = [full_match, full_match + len(text_lower)]
                        # if full_match == 0:
                        #     match_type = 'result_matches_beginning_of_query'
                        # else:
                        match_type = "result_is_substring_of_query"
                    else:
                        partial_match = text_lower.find(last_word_lower)
                        if partial_match != -1:
                            i = len(query_lower) - 1
                            j = len(text_lower) - 1
                            while query_lower[i] == text_lower[j] and i >= 0 and j >= 0:
                                i -= 1
                                j -= 1
                            if len(query_lower) - i > len(last_word_lower):
                                match_type = "part_of_result_in_query"
                            else:
                                match_type = "last_word_substring"
                            boundaries = [
                                partial_match,
                                partial_match + len(last_word_lower),
                            ]
                        if partial_match == 0:
                            boundaries = [
                                partial_match,
                                partial_match + len(last_word_lower),
                            ]
                            match_type = "last_word_prefix"
                            query_before_last_word = query.split()[:-1]
                            if (
                                " ".join(query_before_last_word).lower()
                                not in text_lower
                            ):
                                text = last_word_re.sub(text, query)

                match_id += 1
                match = {
                    "id": match_id,
                    "text": text,
                    "score": term.get("avg_score", {}).get("value", None),
                    "doc_count": term["doc_count"],
                    "field": _type,
                    "match_type": match_type,
                    "match_boundaries": boundaries,
                }
                if match["doc_count"] == 1:
                    match["single_match_document_id"] = term["tops"]["hits"]["hits"][0][
                        "_id"
                    ]
                    match["single_match_document_name"] = term["tops"]["hits"]["hits"][
                        0
                    ]["_source"]["name"]
                if match_type == "last_word_prefix":
                    matching_part = last_word_re.search(text)
                    if matching_part:
                        matching_text = matching_part.group(0)
                        if matching_text.lower() != query_lower:
                            match_copy = match.copy()
                            match_copy["original"] = text
                            match_copy["text"] = matching_text
                            existing_completion = minimal_completions.get(
                                match_copy["text"].lower()
                            )
                            if existing_completion:
                                count = existing_completion["doc_count"]
                            else:
                                count = 0
                            match_copy["doc_count"] = (
                                count + term["doc_count"]
                            )  # todo still don't work
                            match_copy["category"] = "minimal_completion"
                            if match_copy["doc_count"] > 1:
                                try:
                                    del match_copy["single_match_document_id"]
                                    del match_copy["single_match_document_name"]
                                except KeyError:
                                    pass
                            minimal_completions[match_copy["text"].lower()] = match_copy

                if _type == "name" and match_type == "indirect":
                    continue
                if match_type == "part_of_result_in_query":
                    continue
                if match_type == "indirect" or _type == "name":
                    key = _type
                else:
                    key = "completions"
                match["category"] = match["field"]
                suggestions_by_type.setdefault(key, []).append(match)

    # TODO: originally filtered out single-document minimals
    suggestions_by_type["minimal_completions"] = sorted(
        [v for v in minimal_completions.values()],
        key=lambda x: (-x["doc_count"], len(x["text"]), x["text"]),
    )

    last_word_is_ambigious = len(minimal_completions) > 1 and query.lower() in [
        s["text"].lower() for s in minimal_completions.values()
    ]
    return {
        "query": query,
        "query_word_count": len(query.split()),
        "ambiguous_last_word": last_word_is_ambigious,
        "incomplete_query": not _matches_complete_word_tokens(result),
        "suggestions": suggestions_by_type,
    }


LIMITS = {
    "minimal_completions": 5,
    "completions": 10,
    "service": 10,
    "name": 5,
    "location": 5,
    "keyword": 5,
}


def output_suggestion(match, query, keyword_match=False):
    if match["match_type"] == "result_is_substring_of_query":
        suggestion = query
    elif (
        match["match_type"] == "indirect"
        and not keyword_match
        and not match.get("rewritten")
    ):
        suggestion = "{} + {}".format(match["text"], query)
    elif (
        match["field"] != "name"
        and match["match_type"] == "last_word_substring"
        and not keyword_match
        and not match.get("rewritten")
    ):
        # We have to replace the last word in the query with the result match
        suggestion = query.replace(query.split()[-1], match["text"])
    else:
        suggestion = match["text"]
    return {"suggestion": suggestion, "count": match.get("doc_count")}


def query_found_as_keyword(suggestions, query):
    query_lower = query.lower()

    def exact_keyword_match(match):
        return (
            match["field"] == "keyword"
            and match["match_type"] == "full_query_match"
            and match["text"].lower() == query_lower
        )

    def partial_service_match(match):
        return (
            match["field"] == "service"
            and match["match_type"] != "indirect"
            and query_lower in match["text"].lower()
        )

    completions = suggestions.get("suggestions", {}).get("completions", [])
    return (
        next((c for c in completions if exact_keyword_match(c)), None) is not None
        and next((c for c in completions if partial_service_match(c)), None) is None
    )


def choose_suggestions(suggestions, limits=LIMITS):
    query = suggestions["query"]
    keyword_match = query_found_as_keyword(suggestions, query)
    if suggestions["incomplete_query"]:
        active_match_types = ["completions", "name"]
    else:
        if keyword_match:
            active_match_types = ["completions", "service", "service", "name"]
        else:
            active_match_types = [
                "completions",
                "service",
                "name",
                "location",
                "keyword",
            ]
    suggestions_by_type = suggestions["suggestions"]

    name_match_ids = set(
        suggestion["single_match_document_id"]
        for suggestion in suggestions_by_type.get("name", [])[0 : limits["name"]]
        if "single_match_document_id" in suggestion
    )

    results = []
    seen = set()
    minimal_results = []

    def rewrite_single_matches_to_unit_name(_type, match):
        if _type != "name" and match.get("single_match_document_id") in name_match_ids:
            return False
        unit_name = match.get("single_match_document_name")
        if unit_name:
            name_match_ids.add(match.get("single_match_document_id"))
            if _type != "name":
                match["original"] = match["text"]
                match["text"] = unit_name
                match["rewritten"] = True
            name_match_ids.add(match.get("single_match_document_id"))
        return True

    if suggestions["query_word_count"] == 1:
        minimal_suggestions = suggestions_by_type.get("minimal_completions", [])
        for index, match in enumerate(
            sorted(
                minimal_suggestions[0 : limits["minimal_completions"]],
                key=lambda x: len(x["text"]),
            )
        ):
            if not rewrite_single_matches_to_unit_name("minimal_completions", match):
                continue
            suggestion = output_suggestion(match, query, keyword_match=keyword_match)
            if suggestion["suggestion"].lower() not in seen:
                seen.add(suggestion["suggestion"])
                minimal_results.append(suggestion)

    for _type in active_match_types:
        for match in suggestions_by_type.get(_type, [])[0 : limits[_type]]:
            if not rewrite_single_matches_to_unit_name(_type, match):
                continue
            if suggestions["ambiguous_last_word"] and match["match_type"] == "indirect":
                continue
            if match["match_type"] == "indirect" and _type == "keyword":
                continue
            suggestion = output_suggestion(match, query, keyword_match=keyword_match)
            if suggestion["suggestion"].lower() not in seen:
                seen.add(suggestion["suggestion"])
                results.append(suggestion)

    results = minimal_results + results

    return {
        "suggestions": results,
        "requires_completion": suggestions["incomplete_query"],
    }


def suggestion_response(query, language):
    response = requests.get(
        "{}/_search/?search_type=count".format(get_elastic(language)),
        data=json.dumps(suggestion_query(query)),
    )
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

    query["aggs"]["complete_matches"]["filter"]["and"][0]["query"]["query_string"][
        "query"
    ] = "(text:({0}) OR extra_searchwords:({0}))".format(search_query)

    query["query"]["filtered"]["query"] = {
        "match": {"suggest.combined": {"query": search_query}}
    }
    # del query['query']['filtered']['filter']['and'][1]
    filter_query_must = query["query"]["filtered"]["filter"]["and"][1]["query"]["bool"][
        "must"
    ]

    if first_words:
        filter_query_must[0]["match"]["text"]["query"] = first_words
        filter_query_must[1] = {"match": {"suggest.combined": {"query": last_word}}}
    else:
        del query["query"]["filtered"]["filter"]["and"][1]
    return query


def filter_suggestions(suggestions, language):
    words = list(
        set(
            w.strip("()/")
            for suggestion in suggestions["suggestions"]
            for w in suggestion["suggestion"].split()
            if word_is_alphabetic(w)
        )
    )
    query = " ".join(words)
    url = "{}_analyze?analyzer=suggestion_analyze".format(get_elastic(language))
    response = requests.get(url, params={"text": query.encode("utf8")})
    if response.status_code == status.HTTP_404_NOT_FOUND:
        return suggestions
    analyzed_terms = [t["token"] for t in response.json().get("tokens")]
    if len(words) != len(analyzed_terms):
        logger.warning(
            'For the query text "{}", the suggestion analyzer returns the wrong number of terms.'.format(
                query
            )
        )
        logger.warning(
            'Result "{}", the suggestion analyzer returns the wrong number of terms.'.format(
                analyzed_terms
            )
        )
        return suggestions
    analyzed_map = dict(
        (x, y) for x, y in zip(words, analyzed_terms) if x.lower() != y.lower()
    )
    seen = set()
    filtered_suggestions = []
    for suggestion in suggestions["suggestions"]:
        analyzed = tuple(
            analyzed_map.get(w, w).lower() for w in suggestion["suggestion"].split()
        )
        if analyzed not in seen:
            filtered_suggestions.append(suggestion)
            seen.add(analyzed)
    suggestions["suggestions"] = filtered_suggestions
    return suggestions


def clean_query(query):
    query = query.strip()
    if query[-1] == "-":
        query = query.replace("-", "")
    return query


def get_suggestions(query, language):
    query = clean_query(query)
    s = generate_suggestions(query, language)
    if s is None:
        query = re.sub(r"\s+", "", query, flags=re.UNICODE)
        s = generate_suggestions(query, language)
    s = choose_suggestions(s)
    if language == "fi":
        s = filter_suggestions(s, language)
    return s


# The functions below are used for interactive debugging and testing in the console


def _p(val):
    if val:
        pprint.pprint(val, width=100)


def _f(q):
    language = "fi"
    # _p(suggestion_query(q))
    # _p(suggestion_response(q, language))
    suggestions = generate_suggestions(q, language)
    if suggestions is None:
        q = q.replace(" ", "")
        suggestions = generate_suggestions(q, language)
    chosen_suggestions = choose_suggestions(suggestions)
    filtered_suggestions = filter_suggestions(chosen_suggestions, language)
    # pprint.pprint(suggestions)
    # pprint.pprint(chosen_suggestions)
    for s in filtered_suggestions["suggestions"]:
        if s["count"]:
            print("{} ({} toimipistettä)".format(s["suggestion"], s["count"]))
        else:
            print(s["suggestion"])


def _loop():
    while True:
        q = input("\nsearch: ")
        if q == "" or q == ".":
            break
        elif q[-1] == "?":
            try:
                results = unit_results(q[:-1])
                for r in results:
                    print(
                        r["name"]["fi"],
                        "https://palvelukartta.hel.fi/unit/{}".format(r["id"]),
                        r["score"],
                    )
                print(len(results))
            except requests.exceptions.ConnectionError:
                print("Error connecting to smbackend api")
        else:
            _f(q)
