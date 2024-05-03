import io
import logging
import os
import re
import tempfile
import zipfile
from enum import Enum

import requests
import yaml
from django import db
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    PostalCodeArea,
    Street,
)

from mobility_data.models import ContentType, DataSource, MobileUnit
from services.models import Unit

logger = logging.getLogger("mobility_data")

# 11 = Southwest Finland
GEOMETRY_ID = 11
GEOMETRY_URL = (
    "https://tie.digitraffic.fi/api/traffic-message/v1/area-geometries/"
    + f"{GEOMETRY_ID}?includeGeometry=true"
)


class MobileUnitDataBase:
    # Base class for mobile data importers data objects.
    # By inheriting this class the generic save_to_database function can be used
    # to save a list containing objects.
    LANGUAGES = ["fi", "sv", "en"]

    def __init__(self):
        self.name = {lang: None for lang in LANGUAGES}
        self.address = {lang: None for lang in LANGUAGES}
        self.description = {lang: None for lang in LANGUAGES}
        self.municipality = None
        self.address_zip = None
        self.geometry = None
        self.extra = {}
        self.unit_id = None


def get_root_dir():
    """
    Returns the root directory of the project.
    """
    if hasattr(settings, "PROJECT_ROOT"):
        return settings.PROJECT_ROOT
    else:
        return settings.BASE_DIR


CONTENT_TYPES_CONFIG_FILE = (
    f"{get_root_dir()}/mobility_data/importers/data/content_types.yml"
)


LANGUAGES = ["fi", "sv", "en"]


class FieldTypes(Enum):
    STRING = 1
    MULTILANG_STRING = 2
    INTEGER = 3
    FLOAT = 4
    BOOLEAN = 5


class ZippedShapefileDataSource:
    tmp_path = tempfile.gettempdir()

    def __init__(self, zip_url):
        self.zip_path = None
        self.data_source = None
        self.zip_url = zip_url
        response = requests.get(zip_url, stream=True)
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            zip_file.extractall(self.tmp_path)
            self.file_names = zip_file.namelist()
            self.zip_path = self.tmp_path + "/" + self.file_names[0].split("/")[0]
            self.data_source = GDALDataSource(self.zip_path)

    def clean(self):
        for file in self.file_names:
            os.remove(f"{self.tmp_path}/{file}")
        if os.path.exists(self.zip_path):
            os.rmdir(self.zip_path)


def fetch_json(url):
    response = requests.get(url)
    assert response.status_code == 200, "Fetching {} status code: {}".format(
        url, response.status_code
    )
    return response.json()


@db.transaction.atomic
def delete_mobile_units(type_name):
    MobileUnit.objects.filter(content_types__type_name=type_name).delete()


def get_or_create_content_type(name, description):
    content_type, created = ContentType.objects.get_or_create(
        name=name, description=description
    )
    return content_type, created


def get_closest_street_name(point):
    """
    Returns the name of the street that is closest to point.
    """
    address = get_closest_address(point)
    try:
        street = Street.objects.get(id=address.street_id)
        return street.name
    except Street.DoesNotExist:
        return None


def get_closest_address_full_name(point):
    """
    Returns multilingual dict full_name,
    e.g. {"fi": Linnakatu 10,"sv": Slottsgata 10, "en": Linnakatu 10}
     of the closest address to the point.
    """
    address = get_closest_address(point)

    full_name = {
        "fi": address.full_name_fi,
        "sv": address.full_name_sv,
        "en": address.full_name_en,
    }
    return full_name


def get_closest_address(point):
    """
    Return the closest address to the point.
    """
    address = (
        Address.objects.annotate(distance=Distance("location", point))
        .order_by("distance")
        .first()
    )
    return address


def get_postal_code(point):
    """
    Returns the clostest known postal code for the given point.
    """
    address = get_closest_address(point)
    try:
        postal_code_area = PostalCodeArea.objects.get(id=address.postal_code_area_id)
    except PostalCodeArea.DoesNotExist:
        return None
    return postal_code_area.postal_code


def get_street_name_translations(name, municipality):
    """
    Returns a dict where the key is the language and the value is
    the translated name of the street.
    Note, there are no english names for streets and if translation
    does not exist return "fi" name as default name. If street is not found
    return the input name of the street for all languages.
    """
    names = {}
    default_attr_name = "name_fi"
    try:
        street = Street.objects.get(name=name, municipality=municipality)
        for lang in LANGUAGES:
            attr_name = "name_" + lang
            name = getattr(street, attr_name)
            if name:
                names[lang] = name
            else:
                names[lang] = getattr(street, default_attr_name)
        return names
    except Street.DoesNotExist:
        for lang in LANGUAGES:
            names[lang] = name
        return names


def get_municipality_name(point):
    """
    Returns the string name of the municipality in which the point
    is located.
    """
    try:
        muni_type = AdministrativeDivisionType.objects.get(type="muni")
    except AdministrativeDivisionType.DoesNotExist:
        return None
    try:
        geometry = AdministrativeDivisionGeometry.objects.get(
            division__type=muni_type, boundary__contains=point
        )
    except AdministrativeDivisionGeometry.DoesNotExist:
        return None
    try:
        # Get the division from the geometry and return its name.
        return AdministrativeDivision.objects.get(id=geometry.division_id).name
    except AdministrativeDivision.DoesNotExist:
        return None


def set_translated_field(obj, field_name, data):
    """
    Sets the value of all languages for given field_name.
    :param obj: the object to which the fields will be set
    :param field_name:  name of the field to be set.
    :param data: dictionary where the key is the language and the value is the value
    to be set for the field with the given langauge.
    """
    for lang in LANGUAGES:
        if lang in data:
            obj_key = "{}_{}".format(field_name, lang)
            setattr(obj, obj_key, data[lang])


def get_street_name_and_number(address):
    """
    Parses and returns the street name and number from address.
    """
    tmp = re.split(r"(^[^\d]+)", address)
    street_name = tmp[1].rstrip()
    street_number = tmp[2]
    return street_name, street_number


def locates_in_turku(feature, source_data_srid):
    """
    Returns True if the geometry of the feature is inside the boundaries
    of Turku.
    """

    division_turku = AdministrativeDivision.objects.get(name="Turku")
    turku_boundary = AdministrativeDivisionGeometry.objects.get(
        division=division_turku
    ).boundary
    geometry = GEOSGeometry(feature.geom.wkt, srid=source_data_srid)
    geometry.transform(settings.DEFAULT_SRID)
    return turku_boundary.contains(geometry)


def get_file_name_from_data_source(content_type):
    """
    Returns the stored file name in the DataSource table for
    given content type. The name of the file is used by
    the importer when it reads the data.
    """
    data_source_qs = DataSource.objects.filter(type_name=content_type)
    # If data source found, use the uploaded data file name.
    if data_source_qs.exists():
        file_name = str(data_source_qs.first().data_file.file)
        return file_name
    return None


def get_yaml_config(file):
    return yaml.safe_load(open(file, "r", encoding="utf-8"))


def get_content_type_config(type_name):
    configs = get_yaml_config(CONTENT_TYPES_CONFIG_FILE)
    for config in configs.get("content_types", None):
        if type_name == config.get("content_type_name", None):
            if "name" not in config:
                raise Exception(
                    f"Missing name field for {type_name} in {CONTENT_TYPES_CONFIG_FILE}"
                )
            return config
    return None


@db.transaction.atomic
def get_or_create_content_type_from_config(type_name):
    config = get_content_type_config(type_name)
    if config is None:
        raise Exception(
            f"Configuration not found for {type_name} in {CONTENT_TYPES_CONFIG_FILE}"
        )
    queryset = ContentType.objects.filter(type_name=type_name)
    if queryset.count() == 0:
        content_type = ContentType.objects.create(type_name=type_name)
    else:
        content_type = queryset.first()

    for lang in ["fi", "sv", "en"]:
        setattr(content_type, f"name_{lang}", config["name"].get(lang, None))
        if "description" in config:
            setattr(
                content_type,
                f"description_{lang}",
                config["description"].get(lang, None),
            )
    content_type.save()
    return content_type


def log_imported_message(logger, content_type, num_created, num_deleted):
    total_num = MobileUnit.objects.filter(content_types=content_type).count()
    name = content_type.name_en if content_type.name_en else content_type.name_fi
    logger.info(f"Imported {num_created} {name} items of total {total_num}")
    logger.info(f"Deleted {num_deleted} obsolete {name} items")


@db.transaction.atomic
def save_to_database(objects, content_types, logger=logger, group_type=None):
    if type(content_types) != list:
        content_types = [content_types]

    content_types_ids = [ct.id for ct in content_types]
    num_created = 0
    objs_to_delete = list(
        MobileUnit.objects.filter(content_types__in=content_types).values_list(
            "id", flat=True
        )
    )
    for object in objects:
        filter = {
            "name": object.name["fi"],
            "name_sv": object.name["sv"],
            "name_en": object.name["en"],
            "description": object.description["fi"],
            "description_sv": object.description["sv"],
            "description_en": object.description["en"],
            "geometry": object.geometry,
            "address": object.address["fi"],
            "address_sv": object.address["sv"],
            "address_en": object.address["en"],
            "municipality": object.municipality,
            "address_zip": object.address_zip,
            "extra": object.extra,
            "unit_id": object.unit_id,
        }
        queryset = MobileUnit.objects.filter(**filter)
        queryset = queryset.filter(content_types__in=content_types_ids)

        if queryset.count() == 0:
            mobile_unit = MobileUnit.objects.create(**filter)
            num_created += 1
        else:
            if queryset.count() > 1:
                logger.warning(f"Found duplicate MobileUnit {filter}")

            mobile_unit = queryset.first()
            id = queryset.first().id
            if id in objs_to_delete:
                objs_to_delete.remove(id)

        if set(mobile_unit.content_types.all()) != set(
            ContentType.objects.filter(id__in=content_types_ids).all()
        ):
            for content_type in content_types:
                mobile_unit.content_types.add(content_type)

    MobileUnit.objects.filter(id__in=objs_to_delete).delete()
    return num_created, len(objs_to_delete)


def create_mobile_units_as_unit_references(service_id, content_type):
    """
    This function is called by turku_services_importers targets that imports both
    to the services list and mobile view. The created MobileUnits are used to
    serialize the data from the services_unit table in the mobile_unit endpoint.
    """

    units = Unit.objects.filter(services__id=service_id)
    objects = []
    for unit in units:
        obj = MobileUnitDataBase()
        obj.unit_id = unit.id
        objects.append(obj)
    save_to_database(objects, content_type)


def get_full_csv_file_name(csv_file_name, content_type_name):
    file_name = get_file_name_from_data_source(content_type_name)
    if file_name:
        return file_name
    return f"{get_root_dir()}/mobility_data/data/{csv_file_name}"


def split_string_at_first_digit(s):
    match = re.search(r"\d", s)
    if match:
        index = match.start()
        return (
            s[:index],
            s[index:],
        )
    else:
        return s, ""
