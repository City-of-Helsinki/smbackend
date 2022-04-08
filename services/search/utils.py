import libvoikko
from django.db import connection
from django.db.models import Case, When

from services.models import ServiceNode, ServiceNodeUnitCount, Unit
from services.search.constants import (
    DEFAULT_TRIGRAM_THRESHOLD,
    LENGTH_OF_HYPHENATED_WORDS,
    SEARCHABLE_MODEL_TYPE_NAMES,
)

voikko = libvoikko.Voikko("fi")
voikko.setNoUglyHyphenation(True)


def hyphenate(word):
    """
    Returns a list of syllables of the word if word length
    is >= LENGTH_OF_HYPHENATE_WORDS
    """
    word_length = len(word)
    if word_length >= LENGTH_OF_HYPHENATED_WORDS:
        # By Setting the value to word_length, voikko returns
        # the words that are in the compound word, if the word is
        # not a compound word it returns the syllables as normal.
        voikko.setMinHyphenatedWordLength(word_length)
        syllables = voikko.hyphenate(word)
        return syllables.split("-")
    else:
        return [word]


def set_service_node_unit_count(ids, representation):
    """
    As representation is a dict(mutable) passed by the serializer
    set the unit_counts for the service_node.
    """
    unit_counts = {}
    if len(ids) == 1:
        service_node_count_qs = ServiceNodeUnitCount.objects.filter(
            service_node_id=ids[0]
        )
        for service_node_count in service_node_count_qs:
            if hasattr(service_node_count.division, "name"):
                division = service_node_count.division.name_fi.lower()
            else:
                continue
            count = service_node_count.count
            if division in unit_counts:
                unit_counts[division] += count
            else:
                unit_counts[division] = count
    else:
        # Handle grouped service_nodes
        units_qs = Unit.objects.none()
        for id in ids:
            service_node = ServiceNode.objects.get(id=id)
            units_qs = units_qs | service_node.get_units_qs()
        units_qs = units_qs.distinct()

        for unit in units_qs:
            division = unit.municipality_id
            if not division:
                continue
            if division in unit_counts:
                unit_counts[division] += 1
            else:
                unit_counts[division] = 1
    representation["unit_count"] = {"municipality": unit_counts}
    representation["unit_count"]["total"] = sum(unit_counts.values())


def set_service_unit_count(obj, representation):
    """
    As representation is a dict(mutable) passed by the serializer
     set the unit_counts for the service.
    """
    representation["unit_count"] = dict(
        municipality=dict(
            (
                (
                    x.division.name_fi.lower() if x.division else "_unknown",
                    x.count,
                )
                for x in obj.unit_counts.all()
            )
        )
    )
    total = 0
    for _, part in representation["unit_count"]["municipality"].items():
        total += part
    representation["unit_count"]["total"] = total


def set_address_fields(obj, representation):
    """
    Populates mutable dict representation of address related
    fields to the serializer.
    """
    representation["number"] = getattr(obj, "number", "")
    representation["number_end"] = getattr(obj, "number_end", "")
    representation["letter"] = getattr(obj, "letter", "")
    representation["modified_at"] = getattr(obj, "modified_at", "")
    municipality = {
        "id": getattr(obj.street, "municipality_id", ""),
        "name": {},
    }
    municipality["name"]["fi"] = getattr(obj.street.municipality, "name_fi", "")
    municipality["name"]["sv"] = getattr(obj.street.municipality, "name_sv", "")
    representation["municipality"] = municipality
    street = {"name": {}}
    street["name"]["fi"] = getattr(obj.street, "name_fi", "")
    street["name"]["sv"] = getattr(obj.street, "name_sv", "")
    representation["street"] = street


def get_service_node_results(all_results):
    """
    Returns a dict with the aggregated ids. Key is the first id in the results.
    This dict is also sent as context to the serializer to output the ids list.
    """
    ids = {}
    for row in all_results:
        if row[1] == "ServiceNode":
            # Id is the first col and in format type_42_43_44.
            tmp = row[0].split("_")[1:]
            ids[tmp[0]] = tmp[0:]
    return ids


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
    """
    Returns a dict with the model names as keys and the
    object ids of the model as values.
    """
    ids = {}
    for t in SEARCHABLE_MODEL_TYPE_NAMES:
        ids[t] = []
    for row in all_results:
        ids[row[1]].append(row[0].split("_")[1])
    return ids


def get_preserved_order(ids):
    """
    Returns a Case expression that can be used in the order_by method,
    ordering will be equal to the order of ids in the ids list.
    """
    if ids:
        return Case(*[When(id=id, then=pos) for pos, id in enumerate(ids)])
    else:
        return Case()


# def get_trigram_results(model, field, q_val, threshold=0.1):
#     trigm = (
#         model.objects.annotate(
#             similarity=TrigramSimilarity(field, q_val),
#         )
#         .filter(similarity__gt=threshold)
#         .order_by("-similarity")
#     )
#     ids = trigm.values_list("id", flat=True)
#     if ids:
#         preserved = get_preserved_order(ids)
#         return model.objects.filter(id__in=ids).order_by(preserved)
#     else:
#         return model.objects.none()


def get_trigram_results(
    model, model_name, field, q_val, threshold=DEFAULT_TRIGRAM_THRESHOLD
):
    sql = f"""SELECT id, similarity({field}, '{q_val}') AS sml
        FROM {model_name}
        WHERE  similarity({field}, '{q_val}') >= {threshold}
        ORDER BY sml DESC;
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    all_results = cursor.fetchall()

    ids = [row[0] for row in all_results]
    objs = model.objects.filter(id__in=ids)
    return objs
