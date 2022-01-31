import operator
from functools import reduce

from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from services.models import Service, Unit


@receiver(post_save, sender=Unit)
def unit_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    print("Unit on save obj: ", obj)
    # Do transaction after successfull commit.
    transaction.on_commit(populate_search_column(obj))


@receiver(post_save, sender=Service)
def service_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    # print("Service on save obj: ", obj)
    # Do transaction after successfull commit.
    transaction.on_commit(populate_search_column(obj))


def populate_search_column(obj):
    # Get the information of columns and weights to be added to sear from the model
    columns = obj.get_search_column_indexing()
    id = obj.id

    def on_commit():
        search_vectors = []
        for column in columns:
            search_vectors.append(
                SearchVector(column[0], config=column[1], weight=column[2])
            )
        # Add all SearchVectors in searc_vectors list to search_column.
        obj.__class__.objects.filter(id=id).update(
            search_column=reduce(operator.add, search_vectors)
        )

    return on_commit
