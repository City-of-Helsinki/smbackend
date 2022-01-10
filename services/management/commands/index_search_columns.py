from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand

from services.models import Service, ServiceNode, Unit


def get_search_column(model):
    """
    Reads the columns, config languages and weights from the model
    to be indexed. Creates and returns a CombinedSearchVector, that
    can be stored into the search_column.
    """
    search_column = None
    columns = model.get_search_column_indexing()
    for column in columns:
        if search_column:
            search_column += SearchVector(column[0], config=column[1], weight=column[2])
        else:
            search_column = SearchVector(column[0], config=column[1], weight=column[2])

    return search_column


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print(
            "Units indexed:", Unit.objects.update(search_column=get_search_column(Unit))
        )
        print(
            "Services indexed:",
            Service.objects.update(search_column=get_search_column(Service)),
        )
        print(
            "ServiceNodes indexed:",
            ServiceNode.objects.update(search_column=get_search_column(ServiceNode)),
        )
