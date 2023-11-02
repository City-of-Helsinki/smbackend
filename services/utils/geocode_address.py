from geopy.geocoders import Nominatim


def geocode_address(address):
    """
    Geocodes address and returns location coordinates.
    """
    geolocator = Nominatim(user_agent="smbackend")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None
