import logging

from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand
from munigeo.models import Address, AdministrativeDivision

from services.models import Service, Unit

logger = logging.getLogger("search")


def get_search_column(model, lang):
    """
    Reads the columns, config languages and weights from the model
    to be indexed. Creates and returns a CombinedSearchVector, that
    can be stored into the search_column.
    """
    search_column = None
    columns = model.get_search_column_indexing(lang)
    for column in columns:
        if search_column:
            search_column += SearchVector(column[0], config=column[1], weight=column[2])
        else:
            search_column = SearchVector(column[0], config=column[1], weight=column[2])

    return search_column


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        for lang in ["fi", "sv", "en"]:
            key = "search_column_%s" % lang
            logger.info(
                f"{lang} Units indexed: {Unit.objects.update(**{key: get_search_column(Unit, lang)})}"
            )
            logger.info(
                f"{lang} Services indexed: {Service.objects.update(**{key: get_search_column(Service, lang)})}"
            )   
            adm_str = f"{lang} AdministrativeDivisions indexed: " 
            logger.info(
                f"{adm_str}{AdministrativeDivision.objects.update(**{key: get_search_column(AdministrativeDivision, lang)})}"
            )
            logger.info(
                f"{lang} Addresses indexed: {Address.objects.update(**{key: get_search_column(Address, lang)})}"
            )
