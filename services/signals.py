import operator
from functools import reduce

from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from munigeo.models import Address, AdministrativeDivision

from services.models import Service, ServiceNode, Unit
from services.search.utils import hyphenate


@receiver(post_save, sender=Unit)
def unit_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    generate_syllables(obj)
    # Do transaction after successful commit.
    transaction.on_commit(populate_search_column(obj))


@receiver(post_save, sender=Service)
def service_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    populate_service_keywords(obj)
    generate_syllables(obj)
    transaction.on_commit(populate_search_column(obj))


@receiver(post_save, sender=ServiceNode)
def servicenode_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    generate_syllables(obj)
    # To avoid conflicts with Service names, only index if service_reference is None
    if not obj.service_reference:
        transaction.on_commit(populate_search_column(obj))


@receiver(post_save, sender=Address)
def address_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    transaction.on_commit(populate_search_column(obj))


@receiver(post_save, sender=AdministrativeDivision)
def administrative_division_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    transaction.on_commit(populate_search_column(obj))


def generate_syllables(obj):
    model = obj._meta.model
    syllables_fi = []
    for column in obj.get_syllable_fi_columns():
        row_content = getattr(obj, column, None)
        if row_content:
            if isinstance(row_content, str):
                row_content = row_content.split()
            for word in row_content:
                syllables = hyphenate(word)
                for s in syllables:
                    syllables_fi.append(s)
    # Use update instead of save. Save triggers the post_save signal and MPTT building.
    model.objects.filter(id=obj.id).update(syllables_fi=syllables_fi)


def populate_service_keywords(obj):
    keywords = obj.keywords.all()
    keywords_fi, keywords_sv, keywords_en = [], [], []
    for keyword in keywords:
        if keyword.language == "fi":
            keywords_fi.append(keyword.name)
        elif keyword.language == "sv":
            keywords_sv.append(keyword.name)
        else:
            keywords_en.append(keyword.name)
    Service.objects.filter(id=obj.id).update(
        keyword_names_fi=keywords_fi,
        keyword_names_sv=keywords_sv,
        keyword_names_en=keywords_en,
    )


def populate_search_column(obj):
    # Get the information of columns and weights to be added to search from the model
    columns = {}
    columns["fi"] = obj.get_search_column_indexing("fi")
    columns["sv"] = obj.get_search_column_indexing("sv")
    columns["en"] = obj.get_search_column_indexing("en")
    id = obj.id

    def on_commit():
        search_vectors = {}
        for lang in ["fi", "sv", "en"]:
            search_vectors[lang] = []
            for column in columns[lang]:
                search_vectors[lang].append(
                    SearchVector(column[0], config=column[1], weight=column[2])
                )

            # Add all SearchVectors in search_vectors list to search_column.
            key = "search_column_%s" % lang
            obj.__class__.objects.filter(id=id).update(
                **{key: reduce(operator.add, search_vectors[lang])}
            )

    return on_commit
