import requests
from pykml import parser
import re
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
 #   delete_mobile_units, 
 #   fetch_json, 
 #   GEOMETRY_URL
)
URLS = {
    "romantic_turku": {
        "fi": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml&lang=fi",
        "sv": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml&lang=sv",
        "en": "https://citynomadi.com/api/route/4880a6c688c59304b7f6dd21594fbb3d/kml&lang=en"
    },
    "architech_tour":{
        "fi": "https://citynomadi.com/api/route/8ddd24a8fb21f7210da9bb8e3be21967/kml&lang=fi"
    }

}
DEFAULT_SRID = settings.DEFAULT_SRID
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
LANGUAGES = ["fi", "sv", "en"]
class Route:

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

    def __init__(self):
        self.name = {}
        self.description = {}
        self.geometry = None


    def set_data(self,placemark, lang, add_geometry=False):
        
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
                geom = Point(float(x),float(y), srid=4326)
            elif hasattr(placemark, "LineString"):
                str_coords = placemark.LineString.coordinates.text.split("\n")
                coords = []
                for c in str_coords[:-1]: 
                    coord =tuple(map(float, c.split(",")))
                    coords.append(coord)
                geom = LineString(coords, srid=4326)  
            geom.transform(settings.DEFAULT_SRID)

            self.geometry = geom

def get_routes():
    
    #namespace = "{"+doc.nsmap[None]+"}"
    #print(namespace)
    routes = []

    for urls in URLS.values():
        documents = {}
        languages = []
        placemarks = {}
        for lang in urls:
            if lang in LANGUAGES:
                kml_data = requests.get(urls[lang])
                doc = parser.fromstring(kml_data.content)
                languages.append(lang)
                documents[lang] = doc.Document
                placemarks[lang] = doc.Document.Folder.Placemark
        route = Route(documents, languages)
        # add placemarks
        
        pm_objs = []
        for i, lang in enumerate(languages):            
            for c,pm in enumerate(placemarks[lang]):
                add_geometry = False
                if i==0:
                    pm_obj = Placemark()
                    pm_objs.append(pm_obj)
                    add_geometry = True
                else:
                    pm_obj = pm_objs[c]
                pm_obj.set_data(pm, lang, add_geometry=add_geometry)
        route.placemarks += pm_objs   

        routes.append(route)
 
    return routes

def set_translated_field(obj, field_name, data):
    for lang in LANGUAGES:
        if lang in data:
            obj_key = "{}_{}".format(field_name, lang)
            setattr(obj,obj_key, data[lang])

@db.transaction.atomic
def save_to_database(routes, delete_tables=True):  

    group_type, created = GroupType.objects.get_or_create(
            type_name=GroupType.CULTURE_ROUTE,
    )
    MobileUnitGroup.objects.all().delete()
    for route in routes:
        group = MobileUnitGroup(group_type=group_type)
        set_translated_field(group,"name", route.name)
        set_translated_field(group,"description", route.description)
        group.save()
        content_type, _ = get_or_create_content_type(
        ContentType.UNDIFINED, "", "")
  
        for placemark in route.placemarks:
            is_active = True
            mobile_unit = MobileUnit.objects.create(
                is_active=is_active,content_type=content_type, mobile_unit_group=group
            )
            set_translated_field(mobile_unit,"name", placemark.name)
            set_translated_field(mobile_unit,"description", placemark.description)
            mobile_unit.geometry = placemark.geometry
            mobile_unit.save()
    #        breakpoint()
        # create mobileunitgroup