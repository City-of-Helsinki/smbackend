import logging
from datetime import datetime, timedelta

from django.contrib.postgres.search import SearchVector
from django.core.management.base import BaseCommand
from django.utils import timezone
from munigeo.models import Address, AdministrativeDivision

from services.models import Service, ServiceNode, Unit
from services.search.constants import HYPHENATE_ADDRESSES_MODIFIED_WITHIN_DAYS
from services.search.utils import get_foreign_key_attr, hyphenate

logger = logging.getLogger("services.management")


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


def generate_syllables(
    model, hyphenate_all_addresses=False, hyphenate_addresses_from=None
):
    """
    Generates syllables for the given model.
    """
    # Disable sending of signals
    model._meta.auto_created = True
    save_kwargs = {}
    num_populated = 0
    if model.__name__ == "Address" and not hyphenate_all_addresses:
        save_kwargs["skip_modified_at"] = True
        if not hyphenate_addresses_from:
            hyphenate_addresses_from = Address.objects.latest(
                "modified_at"
            ).modified_at - timedelta(days=HYPHENATE_ADDRESSES_MODIFIED_WITHIN_DAYS)
        qs = model.objects.filter(modified_at__gte=hyphenate_addresses_from)
    else:
        qs = model.objects.all()
    for row in qs:
        row.syllables_fi = []
        for column in model.get_syllable_fi_columns():
            row_content = get_foreign_key_attr(row, column)
            if row_content:
                # Rows might be of type str or Array, if str
                # cast to array by splitting.
                if isinstance(row_content, str):
                    row_content = row_content.split()
                for word in row_content:
                    syllables = hyphenate(word)
                    if len(syllables) > 1:
                        for s in syllables:
                            row.syllables_fi.append(s)
                    row.save(**save_kwargs)
            num_populated += 1
    # Enable sending of signals
    model._meta.auto_created = False
    return num_populated


def index_servicenodes(lang):
    """
    Index ServiceNodes which service_reference is null
    to avoid duplicates with Services in results
    """
    service_nodes_indexed = 0
    key = "search_column_%s" % lang
    # Disable sending signals for the model
    ServiceNode._meta.auto_created = True
    columns = ServiceNode.get_search_column_indexing(lang)
    for service_node in ServiceNode.objects.all():
        search_column = None
        if service_node.service_reference is None:
            for column in columns:
                if search_column:
                    search_column += SearchVector(
                        column[0], config=column[1], weight=column[2]
                    )
                else:
                    search_column = SearchVector(
                        column[0], config=column[1], weight=column[2]
                    )
            setattr(service_node, key, search_column)
            service_node.save()
            service_nodes_indexed += 1
    # Enable sending of signals.
    ServiceNode._meta.auto_created = False
    return service_nodes_indexed


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--hyphenate_addresses_from",
            nargs="?",
            type=str,
            help="Hyphenate addresses whose modified_at timestamp starts at given timestamp YYYY-MM-DDTHH:MM:SS",
        )

        parser.add_argument(
            "--hyphenate_all_addresses",
            action="store_true",
            help="Hyphenate all addresses",
        )

    def handle(self, *args, **options):
        hyphenate_all_addresses = options.get("hyphenate_all_addresses", None)
        hyphenate_addresses_from = options.get("hyphenate_addresses_from", None)

        if hyphenate_addresses_from:
            try:
                hyphenate_addresses_from = timezone.make_aware(
                    datetime.strptime(hyphenate_addresses_from, "%Y-%m-%dT%H:%M:%S")
                )
            except ValueError as err:
                raise ValueError(err)
        for lang in ["fi", "sv", "en"]:
            key = "search_column_%s" % lang
            # Only generate syllables for the finnish language
            if lang == "fi":
                logger.info(f"Generating syllables for language: {lang}.")
                logger.info(f"Syllables generated for {generate_syllables(Unit)} Units")
                num_populated = generate_syllables(
                    Address,
                    hyphenate_all_addresses=hyphenate_all_addresses,
                    hyphenate_addresses_from=hyphenate_addresses_from,
                )
                logger.info(f"Syllables generated for {num_populated} Addresses")
                logger.info(
                    f"Syllables generated for {generate_syllables(Service)} Services"
                )
                logger.info(
                    f"Syllables generated for {generate_syllables(ServiceNode)} ServiceNodes"
                )

            logger.info(
                f"{lang} Units indexed: {Unit.objects.update(**{key: get_search_column(Unit, lang)})}"
            )
            logger.info(
                f"{lang} Services indexed: {Service.objects.update(**{key: get_search_column(Service, lang)})}"
            )
            logger.info(f"{lang} ServiceNodes indexed: {index_servicenodes(lang)}")
            logger.info(
                f"{lang} AdministrativeDivisions indexed: "
                f"{AdministrativeDivision.objects.update(**{key: get_search_column(AdministrativeDivision, lang)})}"
            )
            logger.info(
                f"{lang} Addresses indexed: {Address.objects.update(**{key: get_search_column(Address, lang)})}"
            )
