import logging

from django.core.management import BaseCommand

from mobility_data.importers.utils import delete_mobile_units
from mobility_data.models import ContentType

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def add_arguments(self, parser):
        choices = ContentType.objects.all().values_list("name", flat=True)
        parser.add_argument(
            "content_type_names",
            nargs="*",
            choices=choices,
            help="Give names of the content types to be removed as arguments",
        )

    def handle(self, *args, **options):
        for content_type_name in options["content_type_names"]:
            delete_mobile_units(content_type_name)
            logger.info(
                f"Deleted mobile units for content type named: '{content_type_name}'"
            )
