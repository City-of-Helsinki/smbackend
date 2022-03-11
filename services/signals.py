import operator
from functools import reduce

from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from munigeo.models import Address, AdministrativeDivision

from services.models import Service, ServiceNode, Unit


@receiver(post_save, sender=Unit)
def unit_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    # Do transaction after successfull commit.
    transaction.on_commit(populate_search_column(obj))


@receiver(post_save, sender=Service)
def service_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    transaction.on_commit(populate_search_column(obj))


@receiver(post_save, sender=ServiceNode)
def servicenode_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    # To avoid conlicts with Service names onlu index if service_reference is None
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


def populate_search_column(obj):
    # Get the information of columns and weights to be added to sear from the model
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
