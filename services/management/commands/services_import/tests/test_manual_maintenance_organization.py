"""
Tests for the manual_maintenance_organization workaround.

When extensions["manual_maintenance_organization"] is set on a Unit, the importer
must NOT overwrite extensions["maintenance_organization"] with the municipality name.

NOTE: Django's HStoreField stores all values as plain strings.  The flag value must
therefore be the string "True" (not a Python bool or "true"/"1").
"""

import logging
from unittest.mock import MagicMock

import pytest
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import Polygon
from django.utils.timezone import now
from munigeo.importer.sync import ModelSyncher
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)

import services.management.commands.services_import.units as units_module
from services.management.commands.services_import.units import _import_unit
from services.models import Unit

UNIT_ID = 9999


def _make_info(**overrides):
    base = {
        "id": UNIT_ID,
        "name_fi": "Test Unit",
        "name_sv": None,
        "name_en": None,
        "connections": [],
        "accessibility_properties": [],
        "service_details": [],
        "accessibility_viewpoints": "11:unknown",
        "address_city_fi": "Helsinki",
        "is_public": True,
        "dept_id": None,
    }
    base.update(overrides)
    return base


def _make_syncher(unit):
    qs = Unit.objects.filter(id=unit.id)
    syncher = ModelSyncher(qs, lambda obj: obj.id)
    return syncher


def _make_keyword_handler():
    kh = MagicMock()
    kh.sync_searchwords.side_effect = lambda obj, info, changed: changed
    return kh


def _make_dept_syncher():
    ds = MagicMock()
    ds.get.return_value = None  # no department
    return ds


def _bounding_box():
    return Polygon.from_bbox((-180, -90, 180, 90))


def _gps_to_target_ct():
    return CoordTransform(SpatialReference(4326), SpatialReference(4326))


def _call_import_unit(unit, info, municipality=None):
    syncher = _make_syncher(unit)
    # The module uses a global LOGGER; initialise it so calls don't crash.
    units_module.LOGGER = logging.getLogger(__name__)
    muni_by_name = {"helsinki": municipality} if municipality else {}
    _import_unit(
        syncher=syncher,
        keyword_handler=_make_keyword_handler(),
        info=info,
        dept_syncher=_make_dept_syncher(),
        muni_by_name=muni_by_name,
        bounding_box=_bounding_box(),
        gps_to_target_ct=_gps_to_target_ct(),
        target_srid=4326,
        department_id_to_uuid={},
    )
    unit.refresh_from_db()


@pytest.fixture
def helsinki_municipality(db):
    div_type = AdministrativeDivisionType.objects.create(type="muni")
    division = AdministrativeDivision.objects.create(type=div_type, name="Helsinki")
    return Municipality.objects.create(
        id="helsinki", name="Helsinki", division=division
    )


@pytest.fixture
def unit_without_flag(db, helsinki_municipality):
    return Unit.objects.create(
        id=UNIT_ID,
        name="Test Unit",
        last_modified_time=now(),
        extensions={},
    )


@pytest.fixture
def unit_with_flag(db, helsinki_municipality):
    return Unit.objects.create(
        id=UNIT_ID,
        name="Test Unit",
        last_modified_time=now(),
        extensions={
            "manual_maintenance_organization": "True",
            "maintenance_organization": "espoo",
        },
    )


@pytest.mark.django_db
def test_maintenance_organization_set_from_municipality(
    unit_without_flag, helsinki_municipality
):
    _call_import_unit(unit_without_flag, _make_info(), helsinki_municipality)
    unit_without_flag.refresh_from_db()
    assert unit_without_flag.extensions["maintenance_organization"] == "helsinki"


@pytest.mark.django_db
def test_manual_maintenance_organization_not_overwritten(
    unit_with_flag, helsinki_municipality
):
    _call_import_unit(unit_with_flag, _make_info(), helsinki_municipality)
    unit_with_flag.refresh_from_db()
    assert unit_with_flag.extensions["maintenance_organization"] == "espoo"


@pytest.mark.django_db
def test_manual_maintenance_organization_flag_preserved(
    unit_with_flag, helsinki_municipality
):
    _call_import_unit(unit_with_flag, _make_info(), helsinki_municipality)
    unit_with_flag.refresh_from_db()
    assert unit_with_flag.extensions.get("manual_maintenance_organization") == "True"


@pytest.mark.django_db
def test_maintenance_group_default_set(unit_without_flag, helsinki_municipality):
    _call_import_unit(unit_without_flag, _make_info(), helsinki_municipality)
    unit_without_flag.refresh_from_db()
    assert unit_without_flag.extensions["maintenance_group"] == "kaikki"


@pytest.mark.django_db
def test_maintenance_group_not_overwritten_for_manual_unit(
    unit_with_flag, helsinki_municipality
):
    unit_with_flag.extensions.pop("maintenance_group", None)
    unit_with_flag.save()
    _call_import_unit(unit_with_flag, _make_info(), helsinki_municipality)
    unit_with_flag.refresh_from_db()
    assert unit_with_flag.extensions["maintenance_group"] == "kaikki"


@pytest.mark.django_db
@pytest.mark.parametrize("flag_value", ["true", "1", "yes", "TRUE", ""])
def test_only_exact_string_activates_flag(db, helsinki_municipality, flag_value):
    unit = Unit.objects.create(
        id=UNIT_ID,
        name="Test Unit",
        last_modified_time=now(),
        extensions={
            "manual_maintenance_organization": flag_value,
            "maintenance_organization": "espoo",
        },
    )
    _call_import_unit(unit, _make_info(), helsinki_municipality)
    unit.refresh_from_db()
    # The flag was not the exact string "True", so the importer MUST overwrite
    assert unit.extensions["maintenance_organization"] == "helsinki"
