import logging
import re

import lxml
import requests
from django import db
from django.conf import settings
from django.contrib.gis.geos import LineString, Point
from pykml import parser

from mobility_data.models import ContentType, GroupType, MobileUnit, MobileUnitGroup

from .utils import get_or_create_content_type, set_translated_field

logger = logging.getLogger("mobility_data")
# URLS are from https://citynomadi.com/route/?keywords=turku

URLS = {
    "Taidetta Turun katukuvassa": {
        "fi": "https://citynomadi.com/api/route/46d31a6778cee54315ea7c5a0670c0bb/kml?lang=fi",
    },
    "Ruissalo Cultural exercise": {
        "fi": "https://citynomadi.com/api/route/b61d1537ce2743c8f57b0df2ea27b81e/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/b61d1537ce2743c8f57b0df2ea27b81e/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/b61d1537ce2743c8f57b0df2ea27b81e/kml?lang=en",
    },
    "Turku Cathedral": {
        "fi": "https://citynomadi.com/api/route/a200aa6009ce072c52b6175cf7d460a3/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/a200aa6009ce072c52b6175cf7d460a3/kml?lang=sv_SE",
        "en": "https://citynomadi.com/api/route/a200aa6009ce072c52b6175cf7d460a3/kml?lang=en_GB",
    },
    "Stepping it up": {
        "fi": "https://citynomadi.com/api/route/9edfeee48c655d64abfef65fc5081e26/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/9edfeee48c655d64abfef65fc5081e26/kml?lang=sv_SE",
        "en": "https://citynomadi.com/api/route/9edfeee48c655d64abfef65fc5081e26/kml?lang=en_GB",
    },
    "Rmantic Turku": {
        "fi": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml?lang=en",
    },
    "Turku Cathedral Graves Tour": {
        "fi": "https://citynomadi.com/api/route/76c944d7627247b497b1282565a45f46/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/76c944d7627247b497b1282565a45f46/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/76c944d7627247b497b1282565a45f46/kml?lang=en",
    },
    "Ruissalon polut": {
        "fi": "https://citynomadi.com/api/route/24bca7e1839e3fb16133c5afa427016/kml?lang=fi_FI",
    },
    "Katutaidetta Turussa": {
        "fi": "https://citynomadi.com/api/route/e7ed583022c948a484682751013f5eba/kml?lang=fi",
    },
    "Piiloleikki": {
        "fi": "https://citynomadi.com/api/route/152e2f3f6296798468471777a177dbc4/kml?lang=fi_FI",
        "sv": "https://citynomadi.com/api/route/152e2f3f6296798468471777a177dbc4/kml?lang=sv_SE",
    },
    "Suomen Sydän": {
        "fi": "https://citynomadi.com/api/route/13d7ccbfcbbb8d3b725a4b18cd65c48e/kml?lang=fi",
    },
    "Synnin ja oikeuden paikat 1600-luvulla": {
        "fi": "https://citynomadi.com/api/route/925704471104a600a14de4463cddedc8/kml?lang=fi",
    },
    "Turku returns to the map": {
        "fi": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml?lang=en",
    },
    "ArchitecTOUR2": {
        "fi": "https://citynomadi.com/api/route/720780f5828d7c2e7eb924648d1b5dfa/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/720780f5828d7c2e7eb924648d1b5dfa/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/720780f5828d7c2e7eb924648d1b5dfa/kml?lang=en_GB",
    },
    "Sculpture Walk 2": {
        "fi": "https://citynomadi.com/api/route/86a76ceff79c8ef7e3d345964280bc13/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/86a76ceff79c8ef7e3d345964280bc13/kml?lang=sv_SE",
        "en": "https://citynomadi.com/api/route/86a76ceff79c8ef7e3d345964280bc13/kml?lang=en_GB",
    },
    "Naantali walking tour": {
        "fi": "https://citynomadi.com/api/route/a98eff48da3ce9bc52e6ee2d9bf2da6e/kml?lang=fi",
        "en": "https://citynomadi.com/api/route/a98eff48da3ce9bc52e6ee2d9bf2da6e/kml?lang=en_GB",
    },
    "Lost in Turku": {
        "fi": "https://citynomadi.com/api/route/b2724a0a9919f09d4b80b636d663013d/kml?lang=fi",
    },
    "Turun historiallisia puistoja": {
        "fi": "https://citynomadi.com/api/route/6d432b17bcb8f9b99849d4bac91712a4/kml?lang=fi",
    },
    "Kaupunkitarinoita Turusta": {
        "fi": "https://citynomadi.com/api/route/84252a5f01ecc706901452c41896905e/kml?lang=fi",
    },
    "Turku on... miten Turku kohdataan?": {
        "fi": "https://citynomadi.com/api/route/6f83da165fd00d724c5e7b7ae198fe14/kml?lang=fi"
    },
    "Aura River Pilgrimages - The  Way of Peter": {
        "fi": "https://citynomadi.com/api/route/a2994844d064a6874aaeb1c03342ee31/kml?lang=fi",
        "sv": "https://citynomadi.com/api/route/a2994844d064a6874aaeb1c03342ee31/kml?lang=sv",
        "en": "https://citynomadi.com/api/route/a2994844d064a6874aaeb1c03342ee31/kml?lang=en",
    },
    "Jaakontie Renko-Rymättylä": {
        "fi": "https://citynomadi.com/api/route/cf992911d8c170ddf1db528b8cdafcf7/kml?lang=fi"
    },
    "Runosmäen kulttuurikuntoilureitti": {
        "fi": "https://citynomadi.com/api/route/a5d13e38246d44014de725254dbb0167/kml?lang=fi",
    },
    "Seitsämän kirkon reitti Varsinais-Suomessa": {
        "fi": "https://citynomadi.com/api/route/6b26c259c1633b82ecdd1654b5ec0bd7/kml?lang=fi",
    },
    "Selkokielellä Aurajoki, Tuomiokirkko ja Vanha suurtori": {
        "fi": "https://citynomadi.com/api/route/28c7ab229b9416919ddeeb5049f1b01e/kml?lang=fi",
    },
    "Selkokielellä vankila ja Turun Palo": {
        "fi": "https://citynomadi.com/api/route/51e81b4fe148af13305552136def2285/kml?lang=fi"
    },
    "Selkokielellä kirjasto, kauppahalli, apteekkimuseo..": {
        "fi": "https://citynomadi.com/api/route/645788c7fad9d43c5129b3b7bb81b411/kml?lang=fi"
    },
    "Selkokielellä Ruissalo": {
        "fi": "https://citynomadi.com/api/route/b36c19660738055ce5c86988e6dc2fb9/kml?lang=fi",
    },
    "Muistolaattoja Turussa": {
        "fi": "https://citynomadi.com/api/route/717f2d69722d5fcc29f68d7e7427a21b/kml?lang=fi",
    },
    "ArkkitechTOUR 1.0": {
        "fi": "https://citynomadi.com/api/route/8ddd24a8fb21f7210da9bb8e3be21967/kml?lang=fi",
    },
    "Selkokielellä kulttuuria ja urheilua": {
        "fi": "https://citynomadi.com/api/route/37fdd878506c112f60c0af3a8adc7689/kml?lang=fi",
    },
    "Kansallisen kaupunkipuiston pyöräilyreitti": {
        "fi": "https://citynomadi.com/api/route/e2efc96fc87415bf0253148e5e0eae8b/kml?lang=fi",
    },
    "Hitaasti, mutta tyylillä": {
        "fi": "https://citynomadi.com/api/route/4cd8d579c3ef97fee70c65a5361b7395/kml?lang=fi",
    },
    "Sirkushistoriaa ja nykypäivää": {
        "fi": "https://citynomadi.com/api/route/cb91047aca41a401c6515159a9f429e5/kml?lang=fi",
    },
    "Kohtaa Sarja Kuvia, liikennemerkit - Turku 2011": {
        "fi": "https://citynomadi.com/api/route/1e6614d234ef1ac9f3784238cca25b73/kml?lang=fi",
    },
    "Turun kirkkokierros": {
        "fi": "https://citynomadi.com/api/route/9571e7b52db277819c62f0c8b02d2e8a/kml?lang=fi_FI",
    },
    "Pyhän Martin pyhiinvaellusreitti - Raisio": {
        "fi": "https://citynomadi.com/api/route/3aa0c13c18e1976083a4fe9e40376b52/kml?lang=fi",
    },
    "Keskiajan kirkko Turussa": {
        "fi": "https://citynomadi.com/api/route/aa88fafcde2cad8119d855a7a50c701c/kml?lang=fi",
    },
    "Patsastelu 1": {
        "fi": "https://citynomadi.com/api/route/cbef02e5a43dfde2688d7eb75e25cd6b/kml?lang=fi",
    },
    "Linnanniemi": {
        "fi": "https://citynomadi.com/api/route/b43b5ef5056e5a263d460f8b24685472/kml?lang=fi",
        "en": "https://citynomadi.com/api/route/b43b5ef5056e5a263d460f8b24685472/kml?lang=en",
    },
    "Kävele Naiselle Ammatti 2015 - Turku": {
        "fi": "https://citynomadi.com/api/route/6a97c0332d037caa6daa0d1a7029802f/kml?lang=fi"
    },
    "Design Spotting Turku": {
        "fi": "https://citynomadi.com/api/route/26bc00c9582199494c9313b8f174dc0b/kml?lang=fi_FI",
        "sv": "https://citynomadi.com/api/route/26bc00c9582199494c9313b8f174dc0b/kml?lang=sv_SE",
        "en": "https://citynomadi.com/api/route/26bc00c9582199494c9313b8f174dc0b/kml?lang=en_GB",
    },
    "Pansion kulttuurikuntoilureitti": {
        "fi": "https://citynomadi.com/api/route/f6b5e27e0e7a6b46438864161838c508/kml?lang=fi",
    },
    "Kohtaa Sarja Kuvia, muovipatsaat - Turku 2011": {
        "fi": "https://citynomadi.com/api/route/f949548c85b7a6bcc62e271049188094/kml?lang=fi_FI",
    },
}
# Regexp used to remove html and & tags.
CLEANR = re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")

LANGUAGES = ["fi", "sv", "en"]
SOURCE_DATA_SRID = 4326


class Route:
    """
    Objects of this type stores the route data inside the Folder tag in the KML
    File. As the various versions of languages are in separate files the fields
    are stored as dictionaries where the language is the key.
    Also contains a list of all placemarks inside the Document tag. Placemarks
    with same geometry but with different languages are combined into one placemark
    object.
    """

    def __init__(self, documents, languages):
        self.name = {}
        self.description = {}
        self.placemarks = []
        for lang in languages:
            name = re.sub(CLEANR, "", documents[lang].name.text)
            self.name[lang] = name
            # Some routes do not have a description
            if documents[lang].description.text:
                description = re.sub(CLEANR, "", documents[lang].description.text)
            else:
                description = ""
            self.description[lang] = description


class Placemark:
    """
    Object of this type contains data that is inside the Placemark tag in the KML
    file. As the various versions of languages are in separate files the fields
    are stored as dictionaries where the language is the key except for the geometry.
    """

    def __init__(self):
        # Dict to store name, the language is the key
        self.name = {}
        self.description = {}
        self.geometry = None

    def set_data(self, placemark, lang, add_geometry=False):
        """
        :param placemark: The placemark element
        :param lang: The language to be set
        :param add_geometry: if True read and set the geometry
        """
        name = getattr(placemark, "name", None)
        if name:
            name = re.sub(CLEANR, "", name.text)
        self.name[lang] = name
        description = getattr(placemark, "description", None)
        if description:
            description = re.sub(CLEANR, "", description.text)
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
            # Add null Island if no geom set.
            if not geom:
                geom = Point(0, 0, srid=SOURCE_DATA_SRID)
            geom.transform(settings.DEFAULT_SRID)
            self.geometry = geom


def get_routes():
    """
    Return a list routes. The list contains objects of type route.
    """
    routes = []
    for key in URLS.keys():
        # dict used to store the content of all language version of the KML files document tag
        documents = {}
        # list of all language versions found trough the URLS dict for the culture route
        languages = []
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
                    logger.error("Could not parse the data from {}".format(url))
                    continue

                languages.append(lang)
                documents[lang] = doc.Document
                # store placemarks for later processing.
                placemarks[lang] = doc.Document.Folder.Placemark
                route_created = True

        if route_created:
            route = Route(documents, languages)
        else:
            continue
        # List to store only one placemark for the every geometry. As the
        # placemarks language versions are combined to one placemark.
        pm_objs = []
        # Iterate through all the languages the culture route has.
        for lang_index, lang in enumerate(languages):
            # Iterate throug all placemark for the language.
            for pm_index, pm in enumerate(placemarks[lang]):
                add_geometry = False
                # if first language, create new object.
                if lang_index == 0:
                    pm_obj = Placemark()
                    pm_objs.append(pm_obj)
                    # Geometry needs to be set only once for the placemark
                    add_geometry = True
                # when object exist, retrieve object to set data for the current language
                else:
                    pm_obj = pm_objs[pm_index]

                pm_obj.set_data(pm, lang, add_geometry=add_geometry)
        # Add placemark objects to the route object.
        route.placemarks += pm_objs
        routes.append(route)
    return routes


@db.transaction.atomic
def save_to_database(routes, delete_tables=False):
    if delete_tables:
        GroupType.objects.filter(type_name=GroupType.CULTURE_ROUTE).delete()

    group_type, _ = GroupType.objects.get_or_create(
        type_name=GroupType.CULTURE_ROUTE,
        name="Culture Route",
        description="Culture Routes in Turku",
    )
    unit_type, _ = get_or_create_content_type(
        ContentType.CULTURE_ROUTE_UNIT,
        "Culture Route MobileUnit",
        "Contains pointdata, name and description of a place in a Culture Route.",
    )
    geometry_type, _ = get_or_create_content_type(
        ContentType.CULTURE_ROUTE_GEOMETRY,
        "Culture Route Geometry",
        "Contains the LineString geometry of the Culture Route.",
    )
    # counter to store how many routes are saved as new
    saved = 0
    # Routes are stored as MobileUnitGroups and Placemarks as MobileUnits
    for route in routes:
        group, created = MobileUnitGroup.objects.get_or_create(
            group_type=group_type, name=route.name["fi"]
        )
        if created:
            set_translated_field(group, "name", route.name)
            set_translated_field(group, "description", route.description)
            group.save()
            saved += 1

        for placemark in route.placemarks:
            content_type = None
            # If the geometry is a Point the content_type is Culture Route MobileUnit
            if isinstance(placemark.geometry, Point):
                content_type = unit_type
            # If the geometry is a LineString we not the content_Type is Culture Route Geometry
            elif isinstance(placemark.geometry, LineString):
                content_type = geometry_type

            mobile_unit, created = MobileUnit.objects.get_or_create(
                content_type=content_type,
                mobile_unit_group=group,
                geometry=placemark.geometry,
            )
            if created:
                mobile_unit.is_active = True
                set_translated_field(mobile_unit, "name", placemark.name)
                set_translated_field(mobile_unit, "description", placemark.description)
                mobile_unit.save()
    return saved
