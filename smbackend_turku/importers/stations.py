from mobility_data.importers.charging_stations import (
    create_charging_station_content_type,
    get_charging_station_objects,
)
from mobility_data.importers.gas_filling_station import (
    create_gas_filling_station_content_type,
    get_filtered_gas_filling_station_objects,
)
from smbackend_turku.importers.utils import BaseExternalSource


class GasFillingStationImporter(BaseExternalSource):
    def __init__(self, config=None, logger=None, test_data=None):
        super().__init__(config)
        self.logger = logger
        self.test_data = test_data

    def import_gas_filling_stations(self):
        self.logger.info("Importing gas filling stations...")
        content_type = create_gas_filling_station_content_type()
        filtered_objects = get_filtered_gas_filling_station_objects(
            json_data=self.test_data
        )
        super().save_objects_as_units(filtered_objects, content_type)


class ChargingStationImporter(BaseExternalSource):
    def __init__(self, logger=None, config=None, importer=None, test_data=None):
        super().__init__(config)
        self.logger = logger
        self.test_data = test_data

    def import_charging_stations(self):
        self.logger.info("Importing charging stations...")
        filtered_objects = get_charging_station_objects(csv_file=self.test_data)
        content_type = create_charging_station_content_type()
        super().save_objects_as_units(filtered_objects, content_type)


def delete_gas_filling_stations(**kwargs):
    importer = GasFillingStationImporter(**kwargs)
    importer.delete_external_source()


def import_gas_filling_stations(**kwargs):
    importer = GasFillingStationImporter(**kwargs)
    importer.import_gas_filling_stations()


def delete_charging_stations(**kwargs):
    importer = ChargingStationImporter(**kwargs)
    importer.delete_external_source()


def import_charging_stations(**kwargs):
    importer = ChargingStationImporter(**kwargs)
    importer.import_charging_stations()
