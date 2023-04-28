import logging

import django.contrib.gis.gdal.geometries as gdalgeometries
from django import db
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_or_create_content_type_from_config,
    locates_in_turku,
    log_imported_message,
    MobileUnitDataBase,
    save_to_database,
)

DEFAULT_SOURCE_DATA_SRID = 3877
DEFAULT_MAX_FEATURES = 1000
DEFAULT_WFS_TYPE = "string"
logger = logging.getLogger("mobility_data")

WFS_URL = "{wfs_url}?service=WFS&request=GetFeature&typeName={wfs_layer}&outputFormat=GML3&maxFeatures={max_features}"


@db.transaction.atomic
def delete_content_type_using_yaml_config(config):
    content_type_name = config["content_type_name"]
    delete_mobile_units(content_type_name)


class MobilityData(MobileUnitDataBase):
    def __init__(self):
        super().__init__()

    def add_feature(self, feature, config):
        create_multipolygon = False
        if "create_multipolygon" in config:
            create_multipolygon = config["create_multipolygon"]

        if "include" in config:
            for attr, value in config["include"].items():
                if attr not in feature.fields:
                    return False
                # None value returns False as they are not the include value.
                if not feature[attr].as_string():
                    return False
                if value not in feature[attr].as_string():
                    return False
        if "exclude" in config:
            for attr, value in config["exclude"].items():
                if attr not in feature.fields:
                    return False
                # If value is None, continue as it is not possible do determine
                # if the value matches.
                if not feature[attr].as_string():
                    continue
                if value in feature[attr].as_string():
                    return False

        if "srid" in config:
            source_srid = config["srid"]
        else:
            source_srid = DEFAULT_SOURCE_DATA_SRID

        if config.get("locates_in_turku", False):
            if not locates_in_turku(feature, source_srid):
                return False

        # If geometry contains multiple polygons and create_multipolygon attribute is True
        # create one multipolygon from the polygons.
        if (
            len(feature.geom.coords) > 1
            and create_multipolygon
            and isinstance(feature.geom, gdalgeometries.Polygon)
        ):
            polygons = []
            for coords in feature.geom.coords:
                polygons.append(Polygon(coords, srid=source_srid))
            self.geometry = MultiPolygon(polygons, srid=source_srid)
        else:
            self.geometry = GEOSGeometry(feature.geom.wkt, srid=source_srid)
        self.geometry.transform(settings.DEFAULT_SRID)

        if "municipality" in config:
            municipality = feature[config["municipality"]].as_string()
            if municipality:
                municipality_id = municipality.lower()
                self.municipality = Municipality.objects.filter(
                    id=municipality_id
                ).first()

        if "fields" in config:
            for attr, field in config["fields"].items():
                for lang, field_name in field.items():
                    # attr can have fallback definitons if None
                    if getattr(self, attr)[lang] is None:
                        getattr(self, attr)[lang] = feature[field_name].as_string()

        if "extra_fields" in config:
            for field, attr in config["extra_fields"].items():
                val = None

                if "wfs_field" in attr:
                    wfs_field = attr["wfs_field"]
                else:
                    logger.warning(f"No 'wfs_field' defined for {config}.")
                    return False

                if wfs_field in feature.fields:
                    if "wfs_type" in attr:
                        wfs_type = attr["wfs_type"]
                    else:
                        wfs_type = DEFAULT_WFS_TYPE
                    match wfs_type:
                        case "double":
                            val = feature[wfs_field].as_double()
                        case "int":
                            val = feature[wfs_field].as_int()
                        case "string":
                            val = feature[wfs_field].as_string()
                        case _:
                            logger.warning(
                                f"Unrecognizable 'wfs_type' {wfs_type}, using 'string'."
                            )
                            val = feature[wfs_field].as_string()
                self.extra[field] = val
        return True


def import_wfs_feature(config, data_file=None):
    max_features = DEFAULT_MAX_FEATURES
    if "content_type_name" not in config:
        logger.warning(f"Skipping feature {config}, 'content_type_name' is required.")
        return False
    if "wfs_layer" not in config:
        logger.warning(f"Skipping feature {config}, no wfs_layer defined.")
        return False
    if "max_features" in config:
        max_features = config["max_features"]
    wfs_layer = config["wfs_layer"]
    objects = []
    if data_file:
        ds = DataSource(data_file)
    else:
        wfs_url = config.get("wfs_url", settings.TURKU_WFS_URL)

        url = WFS_URL.format(
            wfs_url=wfs_url, wfs_layer=wfs_layer, max_features=max_features
        )
        ds = DataSource(url)
    assert len(ds) == 1
    layer = ds[0]
    for feature in layer:
        object = MobilityData()
        if object.add_feature(feature, config):
            objects.append(object)
    content_type = get_or_create_content_type_from_config(config["content_type_name"])
    num_ceated, num_deleted = save_to_database(objects, content_type)
    log_imported_message(logger, content_type, num_ceated, num_deleted)
