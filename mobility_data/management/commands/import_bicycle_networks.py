import logging

from mobility_data.importers.bicycle_networks import (
    import_brush_salted_bicycle_network,
    import_brush_sanded_bicycle_network,
)

from ._base_import_command import BaseImportCommand

logger = logging.getLogger("mobility_data")


class Command(BaseImportCommand):
    def handle(self, *args, **options):
        logger.info("Importing brush salted bicycle network.")
        import_brush_salted_bicycle_network()
        logger.info("Importing brush sanded bicycle network.")
        import_brush_sanded_bicycle_network()
