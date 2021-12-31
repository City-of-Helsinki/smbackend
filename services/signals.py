from functools import reduce
import operator
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.conf  import settings
from services.models import (
    Unit,
    Service,
    ServiceNode
)

LANGUAGES = {k:v.lower() for k,v in settings.LANGUAGES}

@receiver(post_save, sender=Unit)
def unit_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    print("Unit on save obj: ", obj)
    # Do transaction after successfull commit.
    transaction.on_commit(populate_vector_column(obj))

@receiver(post_save, sender=Service)
def service_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    print("Service on save obj: ", obj)
    # Do transaction after successfull commit.
    transaction.on_commit(populate_vector_column(obj))

@receiver(post_save, sender=ServiceNode)
def service_node_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    print("ServiceNode On save obj: ", obj)
    # Do transaction after successfull commit.
    transaction.on_commit(populate_vector_column(obj))

def get_config_language(col_name):
    # split the col name to get the language
    # e.g. col_name "name_fi" returns "finnish"
    tmp = col_name.split("_")
    if len(tmp)==2:
        return LANGUAGES[tmp[1]]
    else:
        return None

def populate_vector_column(obj):
    # Get the information of columns and weights to be added to sear from the model
    columns = obj.get_vector_column_indexing()
    id = obj.id
    def on_commit():
        search_vectors = []
        for column in columns:
            search_vectors.append(
                SearchVector(column[0], config=column[1], weight=column[2])
            )
        # Add all SearchVectors in searc_vectors list to vector_column.      
        obj.__class__.objects.filter(id=id).update(
            vector_column=reduce(operator.add, search_vectors)
        )
    return on_commit


