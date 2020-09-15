import logging

from django.core.management import BaseCommand

from ptv.importers.ptv import PTVImporter


class Command(BaseCommand):
    help = "Import units and services from PTV"

    def add_arguments(self, parser):
        parser.add_argument("area_codes", nargs="+", type=str)

    def handle(self, *args, **options):
        for area_code in options["area_codes"]:
            logger = logging.getLogger(__name__)
            importer = PTVImporter(area_code=area_code, logger=logger)
            importer.import_municipality_data()
