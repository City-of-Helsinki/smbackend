import logging

import shapefile
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, LineString, Point
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    log_imported_message,
    MobileUnitDataBase,
    save_to_database,
)

from .constants import SOUTHWEST_FINLAND_GEOMETRY

logger = logging.getLogger("mobility_data")
SOUTHWEST_FINLAND_GEOMETRY.transform(settings.DEFAULT_SRID)
DEFAULT_ENCODING = "utf-8"


class MobilityData(MobileUnitDataBase):
    def __init__(self):
        super().__init__()

    def validate_coords(self, coords):
        for coord in coords:
            if abs(coord) > 1_000_000_000:
                return False
        return True

    def add_feature(self, feature, config, srid):
        # Do not add feature if include value does not match.
        if "include" in config:
            for attr, value in config["include"].items():
                if value not in feature.record[attr]:
                    return False
        # Do not add feature if execlude value matches.
        if "exclude" in config:
            for attr, value in config["exclude"].items():
                if value in feature.record[attr]:
                    return False
        geometry = None
        match feature.shape.shapeTypeName:
            case "POLYLINE":
                geometry = LineString(feature.shape.points, srid=srid)
            case "POINT" | "MULTIPOINTZ":
                points = feature.shape.points[0]
                assert len(points) == 2
                geometry = Point(points[0], points[1], srid=srid)
                # The source data can containt invalid point data
                # e.g., (-1.7976931348623157e+308, -1.7976931348623157e+308)
                if not self.validate_coords(geometry.coords):
                    logger.warning(f"Found invalid geometry {feature}")
                    return False
            case _:
                logger.warning(
                    f"Unsuported geometry type {feature.shape.shapeTypeName} in {config}"
                )
                return False

        if geometry.srid != settings.DEFAULT_SRID:
            geometry.transform(settings.DEFAULT_SRID)
        try:
            self.geometry = GEOSGeometry(geometry.wkt, srid=settings.DEFAULT_SRID)
        except Exception as e:
            logger.warning(f"Skipping feature {feature.geom}, invalid geom {e}")
            return False

        if config.get("filter_by_southwest_finland", False):
            if not SOUTHWEST_FINLAND_GEOMETRY.covers(geometry):
                return False

        if "municipality" in config:
            municipality = feature.record[config["municipality"]]
            if municipality:
                municipality_id = municipality.lower()
                self.municipality = Municipality.objects.filter(
                    id=municipality_id
                ).first()

        if "fields" in config:
            for attr, field in config["fields"].items():
                for lang, field_name in field.items():
                    # attr can have  fallback definitons if None
                    if getattr(self, attr)[lang] is None:
                        getattr(self, attr)[lang] = feature.record[field_name]

        if "extra_fields" in config:
            for attr, field in config["extra_fields"].items():
                self.extra[attr] = str(feature.record[field])

        return True


def import_lounaistieto_data_source(config):
    if "content_type_name" not in config:
        logger.warning(
            f"Skipping data source {config}, 'content_type_name' is required."
        )
        return False
    if "data_url" not in config:
        logger.warning(f"Skipping data source {config}, missing 'data_url'")
        return False
    logger.info(f"Importing {config['content_type_name']}")

    if "encoding" in config:
        encoding = config["encoding"]
    else:
        encoding = DEFAULT_ENCODING
        logger.info(f"No encoding defined, using default: {DEFAULT_ENCODING}")
    if "srid" in config:
        srid = config["srid"]
    else:
        srid = settings.DEFAULT_SRID
        logger.info(
            f"No 'srid' configuration found setting default: '{settings.DEFAULT_SRID}'"
        )
    objects = []
    sf = shapefile.Reader(config["data_url"], encoding=encoding)
    for feature in sf.shapeRecords():
        obj = MobilityData()
        if obj.add_feature(feature, config, srid):
            objects.append(obj)
    content_type = get_or_create_content_type_from_config(config["content_type_name"])
    num_created, num_deleted = save_to_database(objects, content_type)
    log_imported_message(logger, content_type, num_created, num_deleted)
