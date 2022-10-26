import logging

from django import db
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    delete_mobile_units,
    get_or_create_content_type,
    set_translated_field,
    ZippedShapefileDataSource,
)
from mobility_data.models import ContentType, MobileUnit

logger = logging.getLogger("mobility_data")


class MobilityData:
    def __init__(self):
        self.extra = {}
        self.name = {}
        self.name = {"fi": None, "sv": None, "en": None}
        self.address = {"fi": None, "sv": None, "en": None}
        self.geometry = None
        self.municipality = None

    def add_feature(self, feature, config):
        try:
            # Do not add feature if include value matches.
            if "include" in config:
                for attr, value in config["include"].items():
                    if value not in feature[attr].as_string():
                        return False
            # Do not add feature if execlude value matches.
            if "exclude" in config:
                for attr, value in config["exclude"].items():
                    if value in feature[attr].as_string():
                        return False

            geometry = feature.geom
            if geometry.srid != settings.DEFAULT_SRID:
                geometry.transform(settings.DEFAULT_SRID)

            try:
                self.geometry = GEOSGeometry(geometry.wkt, srid=settings.DEFAULT_SRID)
            except Exception as e:
                logger.warning(f"Skipping feature {feature.geom}, invalid geom {e}")
            if "municipality" in config:
                municipality = feature[config["municipality"]].as_string()
                if municipality:
                    municipality_id = municipality.lower()
                    self.municipality = Municipality.objects.filter(
                        id=municipality_id
                    ).first()

            for attr, field in config["fields"].items():
                for lang, field_name in field.items():
                    # attr can have  fallback definitons if None
                    if getattr(self, attr)[lang] is None:
                        getattr(self, attr)[lang] = feature[field_name].as_string()
            if "extra_fields" in config:
                for attr, field in config["extra_fields"].items():
                    self.extra[attr] = feature[field].as_string()

        # TODO find a solution for this?
        # Catch exception, as_string() method fails for unknown reasons
        # 'utf-8' codec can't decode byte 0xf6 in position 64: invalid start byte
        except Exception as e:
            logger.warning(f"Skipping feature {feature} {e}")
            return False
        return True


@db.transaction.atomic
def get_and_create_datasource_content_type(config):
    if "content_type" not in config or "content_type_name" not in config:
        logger.warning(
            f"Skipping data source {config}, 'content_type' and 'content_type_name' are required."
        )
    if "content_type_description" in config:
        description = config["content_type_description"]
    else:
        description = ""
    name = config["content_type_name"]
    content_type = config["content_type"]
    ct, _ = get_or_create_content_type(
        getattr(ContentType, content_type), name, description
    )
    return ct


@db.transaction.atomic
def delete_content_type(config):
    content_type = config["content_type"]
    delete_mobile_units(getattr(ContentType, content_type))


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
    if "data_url" not in config:
        logger.warning(f"Skipping data source {config}, missing 'data_url'")
    zip_ds = ZippedShapefileDataSource(config["data_url"])
    objects = []
    assert len(zip_ds.data_source) == 1
    delete_content_type(config)
    layer = zip_ds.data_source[0]
    for i, feature in enumerate(layer):
        obj = MobilityData()
        if obj.add_feature(feature, config):
            objects.append(obj)
    zip_ds.clean()
    save_to_database(objects, config)
    logger.info(f"Saved {len(objects)} {config['content_type_name']} objects.")
