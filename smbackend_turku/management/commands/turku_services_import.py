# -*- coding: utf-8 -*-
import logging
import sys

from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation

from smbackend_turku.importers.accessibility import import_accessibility
from smbackend_turku.importers.addresses import import_addresses
from smbackend_turku.importers.services import import_services
from smbackend_turku.importers.units import import_units


class Command(BaseCommand):
    help = "Import services from City of Turku APIs"
    importer_types = ['services', 'accessibility', 'units', 'addresses']

    supported_languages = [l[0] for l in settings.LANGUAGES]

    def __init__(self):
        super(Command, self).__init__()
        for imp in self.importer_types:
            method = "import_%s" % imp
            assert getattr(self, method, False), "No importer defined for %s" % method

        self.services = {}

        self.options = None
        self.verbosity = 1
        self.logger = None

    def add_arguments(self, parser):
        parser.add_argument('import_types', nargs='*', choices=self.importer_types)
        parser.add_argument('--cached', action='store_true', dest='cached',
                            default=False, help='cache HTTP requests')
        parser.add_argument('--single', action='store', dest='id',
                            default=False, help='import only single entity')

    @db.transaction.atomic
    def import_services(self):
        return import_services(logger=self.logger, importer=self)

    @db.transaction.atomic
    def import_accessibility(self):
        return import_accessibility(logger=self.logger)

    @db.transaction.atomic
    def import_units(self):
        return import_units(logger=self.logger, importer=self)

    @db.transaction.atomic
    def import_addresses(self):
        return import_addresses(logger=self.logger)

    # Activate the default language for the duration of the import
    # to make sure translated fields are populated correctly.
    @translation.override(settings.LANGUAGES[0][0])
    def handle(self, **options):
        self.options = options
        self.verbosity = int(options.get('verbosity', 1))
        self.logger = logging.getLogger(__name__)

        import_count = 0
        for imp in self.importer_types:
            if imp not in self.options["import_types"]:
                continue
            method = getattr(self, "import_%s" % imp)
            if self.verbosity:
                print("Importing %s..." % imp)
            method()
            import_count += 1

        if not import_count:
            sys.stderr.write("Nothing to import.\n")
