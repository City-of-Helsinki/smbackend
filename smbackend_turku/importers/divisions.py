"""
Main parts of the code for this importer has been taken from
https://github.com/City-of-Helsinki/django-munigeo/blob/0.2/munigeo/importer/helsinki.py
and modified to fit the WFS server of Turku.

"""

import os
import re
from datetime import datetime

import yaml
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, DataSource, SpatialReference
from django.contrib.gis.geos import MultiPolygon
from munigeo import ocd
from munigeo.importer.helsinki import poly_diff
from munigeo.importer.sync import ModelSyncher
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
)

from mobility_data.importers.utils import get_root_dir
from smbackend_turku.importers.utils import get_turku_boundary

SOURCE_DATA_SRID = 3877
PROJECTION_SRID = settings.DEFAULT_SRID
SOURCE_DATA_SRS = SpatialReference(SOURCE_DATA_SRID)
PROJECTION_SRS = SpatialReference(PROJECTION_SRID)
WEB_MERCATOR_SRS = SpatialReference(3857)

TURKU_WFS_URL = (
    settings.TURKU_WFS_URL
    + "?service=WFS&request=GetFeature&typeName={layer}&outputFormat=GML3"
)
CONFIG_FILE = "divisions_config.yml"
TURKU_BOUNDARY = get_turku_boundary()


class DivisionImporter:
    def __init__(self, logger=None, importer=None):
        self.logger = logger
        self.importer = importer
        self.muni_data_path = "data"

    def _import_division(self, muni, div, type_obj, syncher, parent_dict, feat):
        check_turku_boundary = div.get("check_turku_boundary", True)
        geom = feat.geom
        if not geom.srid:
            geom.srid = SOURCE_DATA_SRID
        if geom.srid != PROJECTION_SRID:
            ct = CoordTransform(
                SpatialReference(geom.srid), SpatialReference(PROJECTION_SRID)
            )
            geom.transform(ct)

        geom = geom.geos
        if geom.geom_type == "Polygon":
            geom = MultiPolygon(geom.buffer(0), srid=geom.srid)

        # Check if the geometry locates in Turku.
        # As some geometries are not precisely inside the Turku boundarys and some might
        # overlap a bit the Turku boundary even thou the major part is outside the Turku boundarys.
        # So the only way to solve this is by calculating the poly_diff.
        # The value 1_800_000 is chosen heuristically by choosing the biggest value
        # of a geometry that is inside the Turku boundarys.
        if check_turku_boundary:
            p_d = poly_diff(geom, TURKU_BOUNDARY)
            if p_d > 1_800_000:
                return

        #
        # Attributes
        #
        attr_dict = {}
        lang_dict = {}
        for attr, field in div["fields"].items():
            if isinstance(field, dict):
                # Languages
                d = {}
                for lang, field_name in field.items():
                    val = feat[field_name].as_string()
                    # If the name is in all caps, fix capitalization.
                    val = val or ""
                    if not re.search("[a-z]", val):
                        val = val.title()
                    d[lang] = val.strip()
                lang_dict[attr] = d
            else:
                val = feat[field].as_string()
                if val:
                    if (
                        "fields_type_conversions" in div
                        and attr in div["fields_type_conversions"]
                    ):
                        field_type = div["fields_type_conversions"][attr]
                        # We only support csv to list conversions at this moment
                        if field_type == "csv_to_list":
                            attr_dict[attr] = val.strip().split(",")
                    else:
                        attr_dict[attr] = val.strip()
                else:
                    attr_dict[attr] = None

        #
        # Extra attributes
        #
        extra_attr_dict = {}
        if "extra_fields" in div:
            for attr, field in div["extra_fields"].items():
                val = feat[field].as_string()
                if val:
                    extra_attr_dict[attr] = val.strip()
                else:
                    extra_attr_dict[attr] = None

        #
        # Extra attribute-mappings
        #
        if "extra_fields_mappings" in div:
            for field_mapping in div["extra_fields_mappings"]:
                mapping = field_mapping["mapping"]
                attr, field = next(iter(mapping.items()))
                val = str(feat[field].as_string())
                mapped_val = field_mapping["values"][val]
                if mapped_val:
                    extra_attr_dict[attr] = mapped_val.strip()
                else:
                    extra_attr_dict[attr] = None

        attr_dict["extra"] = extra_attr_dict
        """
        ocd-division/country:fi/kunta:turku/äänestysalue:41
        with check_turku_boundary set to false:
        ocd-division/country:fi/Postinumeroalue:21120
        """

        origin_id = attr_dict["origin_id"]

        # if origin_id is not found, we skip the feature
        if not origin_id:
            self.logger.info("Division origin_id is None. Skipping division...")
            return

        if not origin_id:
            self.logger.info("Division origin_id is None. Generating origin_id...")
            return
        if "id_suffix" in div:
            origin_id = origin_id + div["id_suffix"]
        del attr_dict["origin_id"]

        if "parent" in div:
            if "parent_id" in attr_dict:
                parent = parent_dict[attr_dict["parent_id"]]
                del attr_dict["parent_id"]
            else:
                # If no parent id is available, we determine the parent
                # heuristically by choosing the one that we overlap with
                # the most.
                parents = []
                # Calculate diffs
                poly_diffs = [
                    (parent, poly_diff(geom, parent.geometry.boundary))
                    for parent in parent_dict.values()
                ]
                # Sort by diff_area.
                poly_diffs.sort(key=lambda x: x[1])
                # Assign the parent with smallest poly_diff as parent.
                parents.append(poly_diffs[0][0])
                if not parents:
                    raise Exception("No parent found for %s" % origin_id)
                elif len(parents) > 1:
                    raise Exception("Too many parents for %s" % origin_id)
                parent = parents[0]
        elif "parent_ocd_id" in div:
            try:
                parent = AdministrativeDivision.objects.get(ocd_id=div["parent_ocd_id"])
            except AdministrativeDivision.DoesNotExist:
                parent = None
        else:
            parent = muni.division

        if "parent" in div and parent:
            full_id = "%s-%s" % (parent.origin_id, origin_id)
        else:
            full_id = origin_id
        obj = syncher.get(full_id)
        if not obj:
            obj = AdministrativeDivision(origin_id=origin_id, type=type_obj)

        validity_time_period = div.get("validity")
        if validity_time_period:
            obj.start = validity_time_period.get("start")
            obj.end = validity_time_period.get("end")
            if obj.start:
                obj.start = datetime.strptime(obj.start, "%Y-%m-%d").date()
            if obj.end:
                obj.end = datetime.strptime(obj.end, "%Y-%m-%d").date()

        if div.get("no_parent_division", False):
            muni = None

        obj.parent = parent
        obj.municipality = muni

        for attr in attr_dict.keys():
            setattr(obj, attr, attr_dict[attr])
        for attr in lang_dict.keys():
            for lang, val in lang_dict[attr].items():
                key = "%s_%s" % (attr, lang)
                setattr(obj, key, val)
        if "ocd_id" in div:
            assert (parent and parent.ocd_id) or "parent_ocd_id" in div
            if parent:
                if div.get("parent_in_ocd_id", False):
                    ocd_id_args = {"parent": parent.ocd_id}
                else:
                    if check_turku_boundary:
                        ocd_id_args = {"parent": muni.division.ocd_id}
                    else:
                        # If not filtering by Turku boundarys, we only set country as
                        # we can not be sure of the municipality.
                        ocd_id_args = {"country": "fi"}
            else:
                ocd_id_args = {"parent": div["parent_ocd_id"]}
            val = attr_dict["ocd_id"]
            if "id_suffix" in div:
                val = val + div["id_suffix"]
            ocd_id_args[div["ocd_id"]] = val
            obj.ocd_id = ocd.make_id(**ocd_id_args)
            self.logger.debug("%s" % obj.ocd_id)
        obj.save()
        syncher.mark(obj, True)

        try:
            geom_obj = obj.geometry
        except AdministrativeDivisionGeometry.DoesNotExist:
            geom_obj = AdministrativeDivisionGeometry(division=obj)

        geom_obj.boundary = geom
        geom_obj.save()

    def _import_one_division_type(self, muni, div):
        def make_div_id(obj):
            if "parent" in div:
                return "%s-%s" % (obj.parent.origin_id, obj.origin_id)
            else:
                return obj.origin_id

        self.logger.info(div["name"])

        if "origin_id" not in div["fields"]:
            raise Exception(
                "Field 'origin_id' not defined in config section '%s'" % div["name"]
            )
        try:
            type_obj = AdministrativeDivisionType.objects.get(type=div["type"])
        except AdministrativeDivisionType.DoesNotExist:
            type_obj = AdministrativeDivisionType(type=div["type"])
            type_obj.name = div["name"]
            type_obj.save()
        div_qs = AdministrativeDivision.objects.filter(type=type_obj)
        if not div.get("no_parent_division", False):
            div_qs = div_qs.by_ancestor(muni.division).select_related("parent")

        syncher = ModelSyncher(div_qs, make_div_id)
        if "parent" in div:
            parent_list = AdministrativeDivision.objects.filter(
                type__type=div["parent"]
            ).by_ancestor(muni.division)
            parent_dict = {}
            for o in parent_list:
                assert o.origin_id not in parent_dict
                parent_dict[o.origin_id] = o
        else:
            parent_dict = None

        if "wfs_layer" in div:
            url = TURKU_WFS_URL.format(layer=div["wfs_layer"])
            ds = DataSource(url)
            layer = ds[0]
            assert len(ds) == 1
            with AdministrativeDivision.objects.delay_mptt_updates():
                for feat in layer:
                    self._import_division(
                        muni, div, type_obj, syncher, parent_dict, feat
                    )
        else:
            self.logger.warning(
                "Skipping division type %s, no wfs_layer defined." % div
            )

    def import_divisions(self):
        config_path = f"{get_root_dir()}/smbackend_turku/importers/data/"
        path = os.path.join(config_path, CONFIG_FILE)
        config = yaml.safe_load(open(path, "r", encoding="utf-8"))
        self.division_data_path = os.path.join(
            self.muni_data_path, config["paths"]["division"]
        )

        muni = Municipality.objects.get(division__origin_id=config["origin_id"])
        self.muni = muni
        for div in config["divisions"]:
            try:
                self._import_one_division_type(muni, div)
            except Exception as e:
                self.logger.warning("Skipping division %s : %s" % (div, e))


def import_divisions(**kwargs):
    division_importer = DivisionImporter(**kwargs)
    return division_importer.import_divisions()
