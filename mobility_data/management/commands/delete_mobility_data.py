import logging

from django.core.management import BaseCommand

from mobility_data.importers.utils import delete_mobile_units
from mobility_data.models import ContentType

logger = logging.getLogger("mobility_data")


class Command(BaseCommand):
    def get_content_type_full_name(self, content_type):
        for ct in ContentType.CONTENT_TYPES:
            if ct[0] == content_type:
                return ct[1]
        return None

    def add_arguments(self, parser):
        choices = [c[0] for c in ContentType.CONTENT_TYPES]
        # Display the full names of content types in help
        help_choices = [
            f"{str(c)} {self.get_content_type_full_name(c)}" for c in choices
        ]
        help = " ,".join(help_choices)
        parser.add_argument("content_types", nargs="*", choices=choices, help=help)

    def handle(self, *args, **options):
        for content_type in options["content_types"]:
            delete_mobile_units(content_type)
            logger.info(
                f"Deleted mobile units for content type '{content_type}'"
                f" {self.get_content_type_full_name(content_type)}"
            )
