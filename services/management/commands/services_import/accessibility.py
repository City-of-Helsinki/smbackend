import pprint
import json
import hashlib
import logging
from operator import itemgetter
from munigeo.importer.sync import ModelSyncher
from services.models import Unit, AccessibilitySentence
from .utils import pk_get, save_translated_field

VERBOSITY = False
LOGGER = None


def import_accessibility(noop=False, verbosity=True, logger=None):
    global VERBOSITY, LOGGER
    VERBOSITY = verbosity
    LOGGER = logger

    # if VERBOSITY and not LOGGER:
    #    LOGGER = logging.getLogger(__name__)

    obj_list = pk_get('accessibility_sentence')

    if noop:
        return

    sentences_by_unit = {}

    for d in obj_list:
        unit_id = d['unit_id']
        sentence_group = d['sentence_group_name']
        del(d['unit_id'])
        del(d['sentence_group_name'])

        sentences_by_unit.setdefault(unit_id, {})
        sentences_by_unit[unit_id].setdefault(sentence_group, [])
        sentences_by_unit[unit_id][sentence_group].append(d)

    for unit_id, sentences in sentences_by_unit.items():
        unit = Unit.objects.get(pk=unit_id)
        _import_unit_accessibility_sentences(unit, sentences)

    # set hash to None for units without any sentences in input data
    queryset = Unit.objects.exclude(id__in=sentences_by_unit.keys())
    for unit in queryset.filter(accessibility_sentence_hash__isnull=False):
        unit.accessibility_hash = None
        unit.save()

        # remove orphaned sentences
        for as_obj in AccessibilitySentence.objects.filter(unit=unit):
            as_obj.delete()

    print("%s sentences in %s units" % (len(obj_list), len(sentences_by_unit)))


def _import_unit_accessibility_sentences(unit, sentences):
    accs_hash = _accessibility_sentence_hash(sentences)
    # print("unit %s unit, unit.accessibility_sentence_hash, accs_hash)
    if unit.accessibility_sentence_hash == accs_hash:
        return

    # print("unit %s, accssibility sentences changed" % unit)

    for as_obj in AccessibilitySentence.objects.filter(unit__id=unit.id):
        # print("delete:", as_obj, unit.id)
        as_obj.delete()

    for group_name, sentence_list in sentences.items():
        for s in sentence_list:
            as_obj = AccessibilitySentence(unit=unit, group_name=group_name)
            save_translated_field(as_obj, 'group', s, 'sentence_group')
            save_translated_field(as_obj, 'sentence', s, 'sentence')
            as_obj.save()

    unit.accessibility_sentence_hash = accs_hash
    unit.save()


def _accessibility_sentence_hash(sentences):
    # lists of sentences need to be sorted for hashing, sorting on either
    # one alone is not enough to sorting is stable
    for group_name in sentences.keys():
        sentences[group_name] = sorted(sentences[group_name],
                                       key=itemgetter('sentence_group_fi'))
        sentences[group_name] = sorted(sentences[group_name],
                                       key=itemgetter('sentence_fi'))

    sentences_json = json.dumps(sentences, ensure_ascii=False,
                                sort_keys=True).encode('utf8')
    sentences_hash = hashlib.sha1(sentences_json).hexdigest()
    return sentences_hash
