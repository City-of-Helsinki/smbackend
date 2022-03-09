from ptv.importers.ptv_services import PTVServiceImporter
from ptv.importers.ptv_units import UnitPTVImporter


class PTVImporter:
    def __init__(self, area_code, logger):
        self.area_code = area_code
        self.logger = logger

    def import_municipality_data(self):
        """
        Service data depends on the unit data so it needs be imported first.
        """
        unit_importer = UnitPTVImporter(self.area_code)
        unit_importer.import_units()

        service_importer = PTVServiceImporter(self.area_code, self.logger)
        service_importer.import_services()
