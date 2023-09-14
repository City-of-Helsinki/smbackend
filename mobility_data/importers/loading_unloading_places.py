import logging
import re

from django.conf import settings
from django.contrib.gis.gdal import DataSource as GDALDataSource
from django.contrib.gis.geos import GEOSGeometry
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    FieldTypes,
    get_file_name_from_data_source,
    get_root_dir,
    MobileUnitDataBase,
)

logger = logging.getLogger("mobility_data")

SOURCE_DATA_SRID = 3877
GEOJSON_FILENAME = "loading_and_unloading_places.geojson"
LANGUAGES = [language[0] for language in settings.LANGUAGES]
CONTENT_TYPE_NAME = "LoadingUnloadingPlace"


class LoadingPlace(MobileUnitDataBase):
    extra_field_mappings = {
        "Saavutettavuus": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "rajoitukset": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "lastauspiste": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "rajoitustyyppi": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "paikkoja_y": {"type": FieldTypes.INTEGER},
        "max_aika_h": {"type": FieldTypes.STRING},
        "max_aika_m": {"type": FieldTypes.STRING},
        "rajoitus_m": {"type": FieldTypes.STRING},
        "rajoitus_l": {"type": FieldTypes.STRING},
        "rajoitus_s": {"type": FieldTypes.STRING},
        "rajoitettu_ark": {"type": FieldTypes.STRING},
        "rajoitettu_l": {"type": FieldTypes.STRING},
        "rajoitettu_s": {"type": FieldTypes.STRING},
        "voimassaol": {"type": FieldTypes.STRING},
        "varattu_tie_ajoon": {"type": FieldTypes.MULTILANG_STRING},
        "erityisluv": {"type": FieldTypes.MULTILANG_STRING},
        "vuoropys": {"type": FieldTypes.STRING},
        "päiväys": {"type": FieldTypes.STRING},
        "lisätieto": {
            "type": FieldTypes.MULTILANG_STRING,
        },
        "maksuvyöh": {"type": FieldTypes.STRING},
        "rajoit_lis": {"type": FieldTypes.MULTILANG_STRING},
        "talvikunno": {"type": FieldTypes.STRING},
    }

    def __init__(self, feature):
        super().__init__()
        municipality = None
        addresses = [
            " ".join(a.strip().split(" ")[:-2]).rstrip(",")
            for a in feature["Osoite"].as_string().split("/")
        ]
        splitted_addr = feature["Osoite"].as_string().split("/")[0].strip().split(" ")
        # e.g, of 'Osoite' Puolalankatu 8 20100 Turku
        # if lenght of splitted_addr > 3, then we can assume it have
        # zipcode and municipality.
        if len(splitted_addr) > 3:
            self.address_zip, municipality = splitted_addr[-2:]
        names = []
        # Create names from 'Osoite' field
        for n in feature["Osoite"].as_string().split("/"):
            tmp = n.strip().split(" ")
            name = tmp[0].strip()
            for t in tmp[1:]:
                if bool(re.search(r"\d", t)):
                    break
                else:
                    name += f" {t.strip()}"
            names.append(name)

        for i, lang in enumerate(LANGUAGES):
            if i < len(addresses):
                self.address[lang] = addresses[i]
            else:
                # assign Fi if translation not found
                self.address[lang] = addresses[0]
            if i < len(names):
                self.name[lang] = names[i]
            else:
                self.name[lang] = names[0]

        try:
            self.municipality = Municipality.objects.get(name=municipality)
        except Municipality.DoesNotExist:
            self.municipality = None

        self.geometry = GEOSGeometry(feature.geom.wkt, srid=SOURCE_DATA_SRID)
        self.geometry.transform(settings.DEFAULT_SRID)
        self.extra = {}
        for field in feature.fields:
            if field in self.extra_field_mappings:
                # It is possible to define a name in the extra_field_mappings
                # and this name will be used in the extra field and serialized data.
                if hasattr(self.extra_field_mappings[field], "name"):
                    field_name = self.extra_field_mappings[field]["name"]
                else:
                    field_name = field
                match self.extra_field_mappings[field]["type"]:
                    # Source data contains currently only MULTILANG_STRINGs
                    case FieldTypes.MULTILANG_STRING:
                        self.extra[field_name] = {}
                        field_content = feature[field].as_string()
                        if field_content:
                            strings = field_content.split("/")
                            for i, lang in enumerate(LANGUAGES):
                                if i < len(strings):
                                    self.extra[field_name][lang] = strings[i].strip()
                    case FieldTypes.INTEGER:
                        self.extra[field_name] = feature[field].as_int()
                    case FieldTypes.STRING:
                        self.extra[field_name] = feature[field].as_string()


def get_geojson_file_name():
    file_name = get_file_name_from_data_source(CONTENT_TYPE_NAME)
    if file_name:
        return file_name
    return f"{get_root_dir()}/mobility_data/data/{GEOJSON_FILENAME}"


def get_loading_and_unloading_objects():
    objects = []
    file_name = get_geojson_file_name()
    data_layer = GDALDataSource(file_name)[0]
    for feature in data_layer:
        objects.append(LoadingPlace(feature))
    return objects
