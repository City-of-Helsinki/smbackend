from mobility_data.importers.charging_stations import (
    CONTENT_TYPE_NAME as CHARGING_STATION_CONTENT_TYPE_NAME,
    get_charging_station_objects,
)
from mobility_data.importers.gas_filling_station import (
    CONTENT_TYPE_NAME as GAS_FILLING_STATION_CONTENT_TYPE_NAME,
    get_filtered_gas_filling_station_objects,
)
from mobility_data.importers.utils import get_or_create_content_type_from_config
from smbackend_turku.importers.utils import BaseExternalSource


class GasFillingStationImporter(BaseExternalSource):
    def __init__(self, config=None, logger=None):
        super().__init__(config)
        self.logger = logger

    def import_gas_filling_stations(self):
        self.logger.info("Importing gas filling stations...")
        content_type = get_or_create_content_type_from_config(
            GAS_FILLING_STATION_CONTENT_TYPE_NAME
        )
        filtered_objects = get_filtered_gas_filling_station_objects()
        super().save_objects_as_units(filtered_objects, content_type)


class ChargingStationImporter(BaseExternalSource):
    def __init__(self, logger=None, config=None, importer=None):
        super().__init__(config)
        self.logger = logger

    def import_charging_stations(self):
        self.logger.info("Importing charging stations...")
        filtered_objects = get_charging_station_objects()
        content_type = get_or_create_content_type_from_config(
            CHARGING_STATION_CONTENT_TYPE_NAME
        )
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
