import requests
import re
import logging
from pykml import parser
from django import db
from django.conf import settings
from django.contrib.gis.geos import Point, LineString
from mobility_data.models import (
    MobileUnit,
    MobileUnitGroup,
    GroupType,
    ContentType,
    )
from .utils import (
    get_or_create_content_type, 
)

logger = logging.getLogger("mobility_data")
# URLS are from https://www.avoindata.fi/data/dataset/turun-kulttuurikuntoilureitit
URLS = {
    "Romanttinen Turku": {
        "fi": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml&lang=fi",
        "sv": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml&lang=sv",
        "en": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml&lang=en"
    },
    "ArkkitehTOUR": {
        "fi": "https://citynomadi.com/api/route/8ddd24a8fb21f7210da9bb8e3be21967/kml&lang=fi"
    },
    "Ihmeellinen Turku": {
        "fi": "http://citynomadi.com/api/route/bf5bd26d702e64fc433eaa67a74b67a0/kml&lang=fi"
    },
    "Kaupunkitarinoita Turusta": {
        "fi": "https://citynomadi.com/api/route/84252a5f01ecc706901452c41896905e/kml&lang=fi"
    },
    "LOST IN TURKU": {
        "fi": "https://citynomadi.com/api/route/b2724a0a9919f09d4b80b636d663013d/kml&lang=fi"
    },
    "Patsastelu": {
        "fi": "https://citynomadi.com/api/route/cbef02e5a43dfde2688d7eb75e25cd6b/kml&lang=fi"
    },
    "Piiloleikki": {
        "fi": "https://citynomadi.com/api/route/152e2f3f6296798468471777a177dbc4/kml&lang=fi_FI"
    },
    "Porrastelu": {
        "fi": "https://citynomadi.com/api/route/9edfeee48c655d64abfef65fc5081e26/kml&lang=fi"
    },
    "Suomen Sydän": {
        "fi": "https://citynomadi.com/api/route/13d7ccbfcbbb8d3b725a4b18cd65c48e/kml&lang=fi"
    },
    "Turku on": {
        "fi": "https://citynomadi.com/api/route/6f83da165fd00d724c5e7b7ae198fe14/kml&lang=fi"
    },
    "Turku palaa kartalle": {
        "fi": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml&lang=fi",
        "sv": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml&lang=sv",
        "en": "https://citynomadi.com/api/route/832b5ebe5bcef9225dfee8d202db92c0/kml&lang=en"
    },
}

# Regexp used to remove html and & tags.
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

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
            description = re.sub(CLEANR, "", documents[lang].description.text)
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

    def set_data(self,placemark, lang, add_geometry=False):
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
                geom = Point(float(x),float(y), srid=SOURCE_DATA_SRID)
            elif hasattr(placemark, "LineString"):
                str_coords = placemark.LineString.coordinates.text.split("\n")
                coords = []
                # Convert str_coords to tuple format that the LineString 
                # constructor requires.
                for c in str_coords[:-1]: 
                    # typecast to tuple with floats. e.g. '22.2724413872,60.4490541433' ->(22.2724413872,60.4490541433)
                    coord =tuple(map(float, c.split(",")))
                    coords.append(coord)
                geom = LineString(coords, srid=SOURCE_DATA_SRID)  
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
        #list of all language versions found trough the URLS dict for the culture route       
        languages = []
        placemarks = {}
        route_created = False
        for lang in URLS[key]:
            if lang in LANGUAGES:
                url = URLS[key][lang]
                try:
                    kml_data = requests.get(url)
                except requests.ConnectionError:
                    logger.error("URL: {} not found for route: {} and language: {}".format(url, key, lang))
                    continue
                doc = parser.fromstring(kml_data.content)
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
                if lang_index==0:
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

@db.transaction.atomic
def save_to_database(routes, delete_tables=False):     
    if delete_tables:
        GroupType.objects.filter(type_name=GroupType.CULTURE_ROUTE).delete()
    
    group_type, _ = GroupType.objects.get_or_create(
            type_name=GroupType.CULTURE_ROUTE,
            name="Culture Route",
            description="Culture Routes in Turku"
    )
    unit_type, _ = get_or_create_content_type(
        ContentType.CULTURE_ROUTE_UNIT, "Culture Route MobileUnit",
        "Contains pointdata, name and description of a place in a Culture Route.")
    geometry_type, _ = get_or_create_content_type(
        ContentType.CULTURE_ROUTE_GEOMETRY, "Culture Route Geometry",
        "Contains the LineString geometry of the Culture Route.")
    # counter to store how many routes are saved as new
    saved = 0
    # Routes are stored as MobileUnitGroups and Placemarks as MobileUnits
    for route in routes:
        group, created = MobileUnitGroup.objects.get_or_create(
            group_type=group_type,
            name=route.name["fi"])
        if created:
            set_translated_field(group,"name", route.name)
            set_translated_field(group,"description", route.description)
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
                geometry=placemark.geometry
            )
            if created:
                mobile_unit.is_active = True
                set_translated_field(mobile_unit,"name", placemark.name)
                set_translated_field(mobile_unit,"description", placemark.description)
                mobile_unit.save()
    return saved