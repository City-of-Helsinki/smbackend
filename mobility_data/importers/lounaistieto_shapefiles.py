import logging

import shapefile
from django import db
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, LineString, Point
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_or_create_content_type,
    set_translated_field,
)
from mobility_data.models import MobileUnit

logger = logging.getLogger("mobility_data")

DEFAULT_ENCODING = "utf-8"


class MobilityData:
    def __init__(self):
        self.extra = {}
        self.name = {}
        self.name = {"fi": None, "sv": None, "en": None}
        self.address = {"fi": None, "sv": None, "en": None}
        self.geometry = None
        self.municipality = None

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
            case "POINT":
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
        if "municipality" in config:
            municipality = feature.record[config["municipality"]]
            if municipality:
                municipality_id = municipality.lower()
                self.municipality = Municipality.objects.filter(
                    id=municipality_id
                ).first()

        for attr, field in config["fields"].items():
            for lang, field_name in field.items():
                # attr can have  fallback definitons if None
                if getattr(self, attr)[lang] is None:
                    getattr(self, attr)[lang] = feature.record[field_name]

        if "extra_fields" in config:
            for attr, field in config["extra_fields"].items():
                self.extra[attr] = str(feature.record[field])

        return True


@db.transaction.atomic
def get_and_create_datasource_content_type(config):
    if "content_type_description" in config:
        description = config["content_type_description"]
    else:
        description = ""
    name = config["content_type_name"]
    ct, _ = get_or_create_content_type(name, description)
    return ct


@db.transaction.atomic
def delete_content_type(config):
    delete_mobile_units(config["content_type_name"])


@db.transaction.atomic
def save_to_database(objects, config):
    content_type = get_and_create_datasource_content_type(config)
    if not content_type:
        return
    for object in objects:
        mobile_unit = MobileUnit.objects.create(
            content_type=content_type, extra=object.extra, geometry=object.geometry
        )
        mobile_unit.municipality = object.municipality
        set_translated_field(mobile_unit, "name", object.name)
        set_translated_field(mobile_unit, "address", object.address)
        mobile_unit.save()


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
    delete_content_type(config)
    for feature in sf.shapeRecords():
        obj = MobilityData()
        if obj.add_feature(feature, config, srid):
            objects.append(obj)
    save_to_database(objects, config)
    logger.info(f"Saved {len(objects)} {config['content_type_name']} objects.")
