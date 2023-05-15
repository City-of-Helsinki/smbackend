import logging
import re

import lxml
import requests
from django import db
from django.conf import settings
from django.contrib.gis.geos import LineString, Point
from pykml import parser

from mobility_data.models import GroupType, MobileUnit, MobileUnitGroup

from .utils import get_or_create_content_type_from_config, MobileUnitDataBase

logger = logging.getLogger("mobility_data")
# Regexps used to remove html, & tags and css.
CLEANR_HTML = re.compile(
    r"<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});", flags=re.DOTALL
)
CLEANR_CSS = re.compile(r".*\{.*\}", flags=re.DOTALL)
CLEANR_STAR = re.compile(r"^.*/")
LANGUAGES = ["fi", "sv", "en"]
ROUTE_CONTENT_TYPE_NAME = "CultureRouteUnit"
GEOMETRY_CONTENT_TYPE_NAME = "CultureRouteGeometry"
GROUP_CONTENT_TYPE_NAME = "CultureRoute"
SOURCE_DATA_SRID = 4326
# Routes are from https://citynomadi.com/route/?keywords=turku
URLS = {
    "Sotiemme Turku": {
        "fi": "https://citynomadi.com/api/route/fb656ce4fc31868f4b90168ecc3fabdb/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/fb656ce4fc31868f4b90168ecc3fabdb/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/fb656ce4fc31868f4b90168ecc3fabdb/kml?lang=fi",
    },
    "Stepping it up": {
        "fi": "https://citynomadi.com/api/route/9edfeee48c655d64abfef65fc5081e26/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/9edfeee48c655d64abfef65fc5081e26/kml?lang=sv_SE",
        "en": "https://citynomadi.com/api/route/9edfeee48c655d64abfef65fc5081e26/kml?lang=en_GB",
    },
    "Ruissalo Cultural exercise": {
        "fi": "https://citynomadi.com/api/route/b61d1537ce2743c8f57b0df2ea27b81e/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/b61d1537ce2743c8f57b0df2ea27b81e/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/b61d1537ce2743c8f57b0df2ea27b81e/kml?lang=en",
    },
    "Romantic Turku": {
        "fi": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml?lang=en",
    },
    "Sculpture Walk 2": {
        "fi": "https://citynomadi.com/api/route/86a76ceff79c8ef7e3d345964280bc13/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/86a76ceff79c8ef7e3d345964280bc13/kml?lang=sv_SE",
        "en": "https://citynomadi.com/api/route/86a76ceff79c8ef7e3d345964280bc13/kml?lang=en_GB",
    },
    "ArchitecTOUR2": {
        "fi": "https://citynomadi.com/api/route/720780f5828d7c2e7eb924648d1b5dfa/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/720780f5828d7c2e7eb924648d1b5dfa/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/720780f5828d7c2e7eb924648d1b5dfa/kml?lang=en_GB",
    },
    "Suomen Sydän": {
        "fi": "https://citynomadi.com/api/route/13d7ccbfcbbb8d3b725a4b18cd65c48e/kml?lang=fi",
    },
    "Turku on... miten Turku kohdataan?": {
        "fi": "https://citynomadi.com/api/route/6f83da165fd00d724c5e7b7ae198fe14/kml?lang=fi"
    },
    "Turku returns to the map": {
        "fi": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml?lang=en",
    },
    "Kaupunkitarinoita Turusta": {
        "fi": "https://citynomadi.com/api/route/84252a5f01ecc706901452c41896905e/kml?lang=fi",
    },
}


class Route:
    def __init__(self, documents, languages, trailing_number=None):
        self.name = {}
        self.description = {}
        self.placemarks = []
        for lang in languages:
            name = re.sub(CLEANR_HTML, "", documents[lang].name.text)
            # Remove trailing number from Route name
            if name[-1].isdigit():
                name = name[:-1]
            # Remove trailing number and dot, i.e. "2."
            if re.search(r"[0-9]\.$", name):
                name = name[:-2]
            name = name.strip()
            self.name[lang] = name

            if trailing_number:
                self.name[lang] += f" {trailing_number}"
            if documents[lang].description.text:
                description = re.sub(CLEANR_HTML, "", documents[lang].description.text)
                description = re.sub(CLEANR_CSS, "", description)
                description = description.strip()
            else:
                # Some routes do not have a description.
                description = ""
            self.description[lang] = description


class Placemark(MobileUnitDataBase):
    def __init__(self):
        # Store the name and description for every langue to dictionaries
        super().__init__()
        self.content_type = None

    def set_data(self, placemark, lang, add_geometry=False):
        """
        :param placemark: The placemark element
        :param lang: The language to be set
        :param add_geometry: if True read and set the geometry
        """
        name = getattr(placemark, "name", None)
        if name:
            name = re.sub(CLEANR_HTML, "", name.text)
            name = name.strip()
        self.name[lang] = name
        description = getattr(placemark, "description", None)
        if description:
            description = re.sub(CLEANR_HTML, "", description.text)
            description = re.sub(CLEANR_CSS, "", description)
            description = re.sub(CLEANR_STAR, "", description)
            description = description.strip()
        self.description[lang] = description
        if add_geometry:
            geom = None
            if hasattr(placemark, "Point"):
                x, y = placemark.Point.coordinates.text.split(",")
                geom = Point(float(x), float(y), srid=SOURCE_DATA_SRID)
            elif hasattr(placemark, "LineString"):
                # Sourcedata contains empty linestrings.
                if not placemark.LineString.coordinates:
                    geom = None
                else:
                    str_coords = placemark.LineString.coordinates.text.split("\n")
                    coords = []
                    # Convert str_coords to tuple format that the LineString
                    # constructor requires.
                    for c in str_coords[:-1]:
                        # typecast to tuple with floats.
                        # e.g. '22.2724413872,60.4490541433' ->(22.2724413872,60.4490541433)
                        coord = tuple(map(float, c.split(",")))
                        coords.append(coord)
                    # For some reason the sourcedata contains Linestrings with length 1 which is wrong.
                    if len(coords) == 1:
                        geom = Point(coords[0][0], coords[0][1], srid=SOURCE_DATA_SRID)
                    else:
                        geom = LineString(coords, srid=SOURCE_DATA_SRID)
            # Source data contains placemarks without geom?
            # Add null Island if no geometry found.
            if not geom:
                geom = Point(0, 0, srid=SOURCE_DATA_SRID)
            geom.transform(settings.DEFAULT_SRID)
            self.geometry = geom


def get_routes():
    """ "
    The input KML is structued as follow:
    <Document>
        <Folder>
            <Placemark>
            </Placemark>
        </Folder>
    </Document>
    The Document contains the description of the routes. It contains one or more Folders.
    The folders the contains the placemarks of the route. Folders contains one more more Placemarks.
    The placemark are the sights and the geomtry of the route.
    """
    routes = []

    for key in URLS.keys():
        # dict used to store the Document content of all language versions of the KML files.
        documents = {}
        # list of all language versions found trough the URLS dict for the culture route
        languages = []
        # dict containing list of all placemarks in all folders in the document.
        placemarks = {}
        route_created = False
        for lang in URLS[key]:
            if lang in LANGUAGES:
                url = URLS[key][lang]
                try:
                    kml_data = requests.get(url)
                except requests.ConnectionError:
                    logger.error(
                        "URL: {} not found for route: {} and language: {}".format(
                            url, key, lang
                        )
                    )
                    continue
                try:
                    doc = parser.fromstring(kml_data.content)
                except lxml.etree.XMLSyntaxError:
                    logger.error(
                        "Could not parse the data from {} , skipping...".format(url)
                    )
                    continue

                languages.append(lang)
                documents[lang] = doc.Document
                placemarks_to_add = []
                for folder in doc.Document.Folder:
                    if hasattr(folder, "Placemark"):
                        placemarks_to_add.append(folder.Placemark)

                placemarks[lang] = placemarks_to_add
                route_created = True
        if not route_created:
            continue

        logger.info(f"Processing route: {key}.")
        len_folders = len(placemarks["fi"])
        # If placemark["fi"] contains multiple lists, it has multiple folders, i.e. routes.
        # A folder contains the information of one route.
        multiple_routes_in_route = len_folders > 1
        tmp_routes = []
        if multiple_routes_in_route:
            for i in range(0, len_folders):
                tmp_routes.append(Route(documents, languages, trailing_number=i + 1))
        else:
            tmp_routes.append(Route(documents, languages))
        # Iterate trough folders and create placemarks for route(s)
        for folder_index in range(0, len_folders):
            placemarks_to_add = []
            for lang_index, lang in enumerate(languages):
                try:
                    placemarks_in_folder = placemarks[lang][folder_index]
                except IndexError:
                    # in case current language has less folders than in len_folders, skip.
                    # This can occur if swedish and/or english route has for some reason
                    # less routes, i.e. faulty source data.
                    continue

                # Iterate through all Placemarks in folder and set them to route.
                for pm_index, pm in enumerate(placemarks_in_folder):
                    add_geometry = False
                    # if first language, create new object.
                    if lang_index == 0:
                        pm_obj = Placemark()
                        placemarks_to_add.append(pm_obj)
                        # Geometry needs to be set only once for the placemark
                        add_geometry = True
                    else:
                        # else the placemark object exists, retrieve object to set data for the current language
                        pm_obj = placemarks_to_add[pm_index]
                    pm_obj.set_data(pm, lang, add_geometry=add_geometry)
                tmp_routes[folder_index].placemarks += placemarks_to_add

        for route in tmp_routes:
            routes.append(route)
    return routes


@db.transaction.atomic
def save_to_database(routes, delete_tables=False):
    routes_created = 0
    units_created = 0

    if delete_tables:
        GroupType.objects.filter(type_name=GROUP_CONTENT_TYPE_NAME).delete()
    units_to_delete = list(
        MobileUnit.objects.filter(
            mobile_unit_group__group_type__type_name=GROUP_CONTENT_TYPE_NAME
        ).values_list("id", flat=True)
    )
    routes_to_delete = list(
        MobileUnitGroup.objects.filter(
            group_type__type_name=GROUP_CONTENT_TYPE_NAME
        ).values_list("id", flat=True)
    )
    group_type, _ = GroupType.objects.get_or_create(
        type_name=GROUP_CONTENT_TYPE_NAME,
        description="Culture Routes in Turku",
    )
    unit_content_type = get_or_create_content_type_from_config(ROUTE_CONTENT_TYPE_NAME)
    geometry_content_type = get_or_create_content_type_from_config(
        GEOMETRY_CONTENT_TYPE_NAME
    )

    # Routes are stored as MobileUnitGroups and Placemarks as MobileUnits
    for route in routes:
        filter = {
            "name": route.name.get("fi", None),
            "name_sv": route.name.get("sv", None),
            "name_en": route.name.get("en", None),
            "description": route.description.get("fi", None),
            "description_sv": route.description.get("sv", None),
            "description_en": route.description.get("en", None),
            "group_type": group_type,
        }
        queryset = MobileUnitGroup.objects.filter(**filter)
        if queryset.count() == 0:
            group = MobileUnitGroup.objects.create(**filter)
            routes_created += 1

        else:
            group = queryset.first()
            id = group.id
            if id in routes_to_delete:
                routes_to_delete.remove(id)

        for placemark in route.placemarks:
            content_type = None
            # If the geometry is a Point the content_type is Culture Route MobileUnit
            if isinstance(placemark.geometry, Point):
                content_type = unit_content_type
            # If the geometry is a LineString we not the content_Type is Culture Route Geometry
            elif isinstance(placemark.geometry, LineString):
                content_type = geometry_content_type

            filter = {
                "name": placemark.name["fi"],
                "name_sv": placemark.name["sv"],
                "name_en": placemark.name["en"],
                "description": placemark.description["fi"],
                "description_sv": placemark.description["sv"],
                "description_en": placemark.description["en"],
                "geometry": placemark.geometry,
                "mobile_unit_group": group,
                "is_active": True,
            }

            queryset = MobileUnit.objects.filter(**filter)
            if queryset.count() == 0:
                mobile_unit = MobileUnit.objects.create(**filter)
                mobile_unit.content_types.add(content_type)
                units_created += 1
            else:
                id = queryset.first().id
                if id in units_to_delete:
                    units_to_delete.remove(id)
    MobileUnit.objects.filter(id__in=units_to_delete).delete()
    MobileUnitGroup.objects.filter(id__in=routes_to_delete).delete()
    return routes_created, len(routes_to_delete), units_created, len(units_to_delete)
