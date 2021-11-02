import requests
from mobility_data.models import ContentType
GEOMETRY_ID = 11 #  11 Varsinaissuomi 
GEOMETRY_URL = "https://tie.digitraffic.fi/api/v3/data/traffic-messages/area-geometries?id={id}&lastUpdated=false".format(id=GEOMETRY_ID)

def fetch_json(url):
    response = requests.get(url)
    assert response.status_code == 200, "Fetching {} status code: {}".\
            format(url, response.status_code)
    return response.json()

def delete_mobile_units(type_name):
    ContentType.objects.filter(type_name=type_name).delete()

def get_or_create_content_type(type_name, name, description):
    content_type, created = ContentType.objects.get_or_create(
        type_name=type_name,
        name=name,
        description=description
    )
    return content_type, created