from mobility_data.importers.bicycle_stands import (
    create_bicycle_stand_content_type,
    get_bicycle_stand_objects,
)
from smbackend_turku.importers.utils import BaseExternalSource


class BicycleStandImporter(BaseExternalSource):
    def __init__(self, logger=None, config=None, test_data=None):
        super().__init__(config)
        self.logger = logger
        self.test_data = test_data

    def import_bicycle_stands(self):
        self.logger.info("Importing Bicycle Stands...")
        content_type = create_bicycle_stand_content_type()
        filtered_objects = get_bicycle_stand_objects()
        super().save_objects_as_units(filtered_objects, content_type)


def delete_bicycle_stands(**kwargs):
    importer = BicycleStandImporter(**kwargs)
    importer.delete_external_source()


def import_bicycle_stands(**kwargs):
    importer = BicycleStandImporter(**kwargs)
    importer.import_bicycle_stands()
