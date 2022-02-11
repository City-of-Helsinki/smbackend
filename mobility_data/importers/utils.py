import requests
import re
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from munigeo.models import (
    Address,
    Street,
    Municipality,
    AdministrativeDivisionGeometry, 
    AdministrativeDivision,
)
from mobility_data.models import ContentType, MobileUnit

GEOMETRY_ID = 11 #  11 Varsinaissuomi 
GEOMETRY_URL = "https://tie.digitraffic.fi/api/v3/data/traffic-messages/area-geometries?id={id}&lastUpdated=false".format(id=GEOMETRY_ID)
LANGUAGES = ["fi", "sv", "en"]

def fetch_json(url):
    response = requests.get(url)
    assert response.status_code == 200, "Fetching {} status code: {}".\
            format(url, response.status_code)
    return response.json()

def delete_mobile_units(type_name):
    ContentType.objects.filter(type_name=type_name).delete()


def create_mobile_unit_as_unit_reference(unit_id, content_type):
    """
    This function is called by turku_services_importers target that imports both
    to the services list and mobile view. The created MobileUnit is used to
    serialize the data from the services_unit table in the mobile_unit endpoint.
    """
   
    MobileUnit.objects.create(
            unit_id=unit_id,
            content_type=content_type,             
    )

def get_or_create_content_type(type_name, name, description):
    content_type, created = ContentType.objects.get_or_create(
        type_name=type_name,
        name=name,
        description=description
    )
    return content_type, created

def get_closest_street_name(point):
    """
    Returns the name of the street that is closest to point.
    """
    address = Address.objects.annotate(distance=Distance("location", point)).order_by("distance").first()
    try:
        street = Street.objects.get(id=address.street_id)
        return street.name
    except Street.DoesNotExist:
        return None

def get_street_name_translations(name):
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
        street = Street.objects.get(name=name)
        for lang in LANGUAGES:
            attr_name = "name_"+lang
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
        # resolve in which division to point is.
        division = AdministrativeDivisionGeometry.objects.get(boundary__contains=point)
    except AdministrativeDivisionGeometry.DoesNotExist:
        return None
    # Get the division and return its name.
    return AdministrativeDivision.objects.get(id=division.division_id).name

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
    