# -*- coding: utf-8 -*-
import logging
import sys

from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation

from smbackend_turku.importers.accessibility import import_accessibility
from smbackend_turku.importers.addresses import import_addresses
from smbackend_turku.importers.bicycle_stands import (  # noqa: F401
    delete_bicycle_stands,
    import_bicycle_stands,
)
from smbackend_turku.importers.bike_service_stations import (  # noqa: F401
    delete_bike_service_stations,
    import_bike_service_stations,
)
from smbackend_turku.importers.divisions import import_divisions
from smbackend_turku.importers.geo_search import (
    import_enriched_addresses,
    import_geo_search_addresses,
)
from smbackend_turku.importers.services import import_services
from smbackend_turku.importers.stations import (  # noqa: F401
    delete_charging_stations,
    delete_gas_filling_stations,
    import_charging_stations,
    import_gas_filling_stations,
)
from smbackend_turku.importers.units import import_units
from smbackend_turku.importers.utils import get_external_source_config  # noqa: F401
from smbackend_turku.importers.utils import get_configured_external_sources_names

IMPORTER_FUNCTIONS_CODE = """
@db.transaction.atomic
def import_{name}(self):
    config = get_external_source_config("{name}")
    import_{name}(logger=self.logger, config=config)
@db.transaction.atomic
def delete_{name}(self):
    config = get_external_source_config("{name}")
    delete_{name}(logger=self.logger, config=config)
"""


class Command(BaseCommand):
    help = "Import services from City of Turku APIs and from external sources."

    # Umbrella source that imports all external_sources
    EXTERNAL_SOURCES = "external_sources"

    external_sources = get_configured_external_sources_names()
    importer_types = [
        "services",
        "accessibility",
        "units",
        "addresses",
        "geo_search_addresses",
        "enriched_addresses",
        "divisions",
        EXTERNAL_SOURCES,
    ] + external_sources

    supported_languages = [lang[0] for lang in settings.LANGUAGES]

    for name in external_sources:
        code = IMPORTER_FUNCTIONS_CODE.format(name=name)
        exec(code)

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            method = "import_%s" % imp
            assert getattr(self, method, False), "No importer defined for %s" % method

        self.services = {}
        self.options = None
        self.verbosity = 1

    def add_arguments(self, parser):
        # parser.set_conflict_handler("resolve")
        parser.add_argument("import_types", nargs="*", choices=self.importer_types)
        parser.add_argument(
            "--cached",
            action="store_true",
            dest="cached",
            default=False,
            help="cache HTTP requests",
        )
        parser.add_argument(
            "--single",
            action="store",
            dest="id",
            default=False,
            help="import only single entity",
        )
        parser.add_argument(
            "--delete-external-sources",
            action="store_true",
            default=False,
            help="If parameter is set when importing, deletes the external \
                 sources imported with the importer.",
        )

        parser.add_argument(
            "--delete-external-source",
            action="store_true",
            default=False,
            help="If parameter is set when importing, deletes the external \
                 sources given as arguments.",
        )

    @db.transaction.atomic
    def import_services(self):
        return import_services(
            logger=self.logger,
            importer=self,
            delete_external_sources=self.delete_external_sources,
        )

    @db.transaction.atomic
    def import_accessibility(self):
        return import_accessibility(logger=self.logger)

    @db.transaction.atomic
    def import_units(self):
        return import_units(
            logger=self.logger,
            importer=self,
            delete_external_sources=self.delete_external_sources,
        )

    @db.transaction.atomic
    def import_addresses(self):
        return import_addresses(logger=self.logger)

    def import_geo_search_addresses(self):
        return import_geo_search_addresses(logger=self.logger)

    def import_enriched_addresses(self):
        return import_enriched_addresses(logger=self.logger)

    @db.transaction.atomic
    def import_divisions(self):
        return import_divisions(logger=self.logger)

    @db.transaction.atomic
    def import_external_sources(self):
        for name in self.external_sources:
            method = getattr(self, "import_%s" % name)
            method()

    # Activate the default language for the duration of the import
    # to make sure translated fields are populated correctly.
    @translation.override(settings.LANGUAGES[0][0])
    def handle(self, **options):

        self.options = options
        self.verbosity = int(options.get("verbosity", 1))
        self.logger = logging.getLogger("turku_services_import")
        # if set delete all external sources.
        self.delete_external_sources = options.get("delete_external_sources", False)
        # if set delete external sources in arguments
        self.delete_external_source = options.get("delete_external_source", False)

        if self.delete_external_source:
            delete_count = 0
            for imp in self.external_sources:
                if imp not in self.options["import_types"]:
                    continue
                method = getattr(self, "delete_%s" % imp)
                if self.verbosity:
                    print("Deleting %s..." % imp)
                method()
                delete_count += 1
            if not delete_count:
                sys.stderr.write("Nothing to delete.\n")
        else:
            importers = self.options["import_types"]
            if self.EXTERNAL_SOURCES in self.options["import_types"]:
                # Add EXTERNAL_SOURCES by creating a set to ensure there are no duplicates
                # as the user can add args as EXTERNAL_SOURCES charging_stations
                importers = set(importers + self.external_sources)
                # remove the EXTERNAL_SOURCES source as it has no function attached to it.
                importers.remove(self.EXTERNAL_SOURCES)

            import_count = 0
            for imp in self.importer_types:
                if imp not in importers:
                    continue
                method = getattr(self, "import_%s" % imp)
                if self.verbosity:
                    print("Importing %s..." % imp)
                method()
                import_count += 1

            if not import_count:
                sys.stderr.write("Nothing to import.\n")
