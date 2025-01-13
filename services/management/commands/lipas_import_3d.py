import logging

from django.contrib.gis.geos import LineString, MultiLineString

from services.management.commands import lipas_import

logger = logging.getLogger(__name__)

TYPES = {
    "3d_paths_1": "lipas:lipas_4401_kuntorata_3d",
    "3d_paths_2": "lipas:lipas_4402_latu_3d",
    "3d_paths_3": "lipas:lipas_4403_kavelyreitti_3d",
    "3d_paths_4": "lipas:lipas_4404_luontopolku_3d",
    "3d_paths_5": "lipas:lipas_4405_retkeilyreitti_3d",
    "3d_paths_6": "lipas:lipas_4411_maastopyorailyreitti_3d",
    "3d_paths_7": "lipas:lipas_4412_pyorailyreitti_3d",
    "3d_paths_8": "lipas:lipas_4421_moottorikelkkareitti_3d",
    "3d_paths_9": "lipas:lipas_4422_moottorikelkkaura_3d",
    "3d_paths_10": "lipas:lipas_4430_hevosreitti_3d",
    "3d_paths_11": "lipas:lipas_4440_koirahiihtolatu_3d",
    "3d_paths_12": "lipas:lipas_4451_melontareitti_3d",
    "3d_paths_13": "lipas:lipas_4452_vesiretkeilyreitti_3d",
}


class Command(lipas_import.Command):
    def _save_geometries(self, geometries, units_by_lipas_id):
        logger.info("Updating 3D geometries in the database...")
        for lipas_id, geometry in geometries.items():
            unit = units_by_lipas_id[lipas_id]
            if self._has_z_coordinate(geometry):
                try:
                    line_geometry = geometry.merged
                    if isinstance(line_geometry, LineString):
                        line_geometry = MultiLineString([line_geometry])
                    unit.geometry_3d = line_geometry
                    if len(line_geometry) == 0:
                        unit.geometry_3d = geometry
                except TypeError as e:
                    logger.warning(
                        f"Failed to merge 3D geometry for unit {unit.name_fi}: {e}",
                    )
                    unit.geometry_3d = geometry
                unit.save()
            else:
                logger.warning(
                    f"Failed to save unit {unit.name_fi} because of a missing z"
                    " coordinate.",
                )

    def _get_types(self):
        return TYPES

    def _has_z_coordinate(self, geometry):
        """
        Check if a geometry has a Z-coordinate (3D).
        """
        return geometry.hasz
