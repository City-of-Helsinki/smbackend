import requests
import logging
import json
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from iot.models import IoTData
from iot.utils import get_cache_keys
logger = logging.getLogger("iot")
RENT24_CARS_URL = "https://api.24rent.fi/v2/car/search?carId=0&discount=&distance=30000&endDate=09.03.2022&endTime=11:00&key=OWMwZTU0MjIxMDgzOTRmYTAxMTgzOTg5&km=100&lat=60.4518126&lon=22.2666302&originurl=www.24rent.fi&showEnd=10000&showStart=0&startDate=09.03.2022&startTime=09:00"
INFRAROAD_SNOW_PLOW_URL = (
    "https://infraroad.fluentprogress.fi/KuntoInfraroad/v1/snowplow/"
)

url_mappings = {
    IoTData.RENT24_CARS: RENT24_CARS_URL,
    IoTData.INFRAROAD_SNOW_PLOWS: INFRAROAD_SNOW_PLOW_URL,
}


def save_data_to_db(source_name, url):
    IoTData.objects.filter(source_name=source_name).delete()
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not fetch data from: {url}")
        return
    try:
        json_data = response.json()
    except json.decoder.JSONDecodeError:
        logger.error(f"Could not decode data to json from: {url}")
        return
    for row in json_data:
        IoTData.objects.create(source_name=source_name, data=row)


def clear_cache(source_name):
    key_queryset, key_serializer = get_cache_keys(source_name)
    cache.delete_many([key_queryset, key_serializer])


class Command(BaseCommand):
    help = "Import IoT-Data for intermediate storage."
    source_names = IoTData.get_source_names()

    def add_arguments(self, parser):
        parser.add_argument(
            "source_name",
            help=f"Three letter uppercase name of the source to import. Available source names are: {self.source_names} ",
        )

    def handle(self, *args, **options):
        source_name = options["source_name"]
        if source_name not in self.source_names:
            logger.error(f"{source_name} not found, choices are {self.source_names}")
            return
        # Clear cache every time data is imported.
        # This ensures that the data is up to date.
        clear_cache(source_name)
        save_data_to_db(source_name, url_mappings[source_name])
