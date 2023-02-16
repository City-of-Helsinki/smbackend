"""
This management command updates statistical district extra-data from Statistics Finland
"""
import json
import logging
import os
from time import time

import requests
from django.core.management.base import BaseCommand
from munigeo.models import AdministrativeDivision, Municipality

logger = logging.getLogger("services.management")

OCD_ID_STATISTICS_BASE = "ocd-division/country:fi/tilastoalue:"


def get_abs_file_path(json_file):
    script_dir = os.path.dirname(__file__)
    rel_path = "statistical_queries/" + json_file
    return os.path.join(script_dir, rel_path)


HELSINKI_POPULATION_BY_AGE_URL = (
    "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaerak/pksoa/A01S_HKI_Vakiluku.px"
)
with open(get_abs_file_path("helsinki_population_by_age.json")) as f:
    HELSINKI_POPULATION_BY_AGE = json.load(f)

ESPOO_POPULATION_BY_AGE_URL = (
    "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaerak/pksoa/B01S_ESP_Vakiluku.px"
)
with open(get_abs_file_path("espoo_population_by_age.json")) as f:
    ESPOO_POPULATION_BY_AGE = json.load(f)

VANTAA_POPULATION_BY_AGE_URL = (
    "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaerak/pksoa/C01S_VAN_Vakiluku.px"
)
with open(get_abs_file_path("vantaa_population_by_age.json")) as f:
    VANTAA_POPULATION_BY_AGE = json.load(f)


population_by_age_configs = {
    "helsinki": {
        "url": HELSINKI_POPULATION_BY_AGE_URL,
        "data": HELSINKI_POPULATION_BY_AGE,
        "municipality": Municipality.objects.get(name="Helsinki"),
    },
    "espoo": {
        "url": ESPOO_POPULATION_BY_AGE_URL,
        "data": ESPOO_POPULATION_BY_AGE,
        "municipality": Municipality.objects.get(name="Espoo"),
    },
    "vantaa": {
        "url": VANTAA_POPULATION_BY_AGE_URL,
        "data": VANTAA_POPULATION_BY_AGE,
        "municipality": Municipality.objects.get(name="Vantaa"),
    },
}

HELSINKI_POPULATION_FORECAST_URL = "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaenn/pksoa/A01HKIS_Vaestoennuste.px"
with open(get_abs_file_path("helsinki_population_forecast.json")) as f:
    HELSINKI_POPULATION_FORECAST = json.load(f)

ESPOO_POPULATION_FORECAST_URL = "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaenn/pksoa/B01ESPS_Vaestoennuste.px"
with open(get_abs_file_path("espoo_population_forecast.json")) as f:
    ESPOO_POPULATION_FORECAST = json.load(f)

VANTAA_POPULATION_FORECAST_URL = "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaenn/pksoa/C01VANS_Vaestoennuste.px"
with open(get_abs_file_path("vantaa_population_forecast.json")) as f:
    VANTAA_POPULATION_FORECAST = json.load(f)


population_forecast_configs = {
    "helsinki": {
        "url": HELSINKI_POPULATION_FORECAST_URL,
        "data": HELSINKI_POPULATION_FORECAST,
        "municipality": Municipality.objects.get(name="Helsinki"),
    },
    "espoo": {
        "url": ESPOO_POPULATION_FORECAST_URL,
        "data": ESPOO_POPULATION_FORECAST,
        "municipality": Municipality.objects.get(name="Espoo"),
    },
    "vantaa": {
        "url": VANTAA_POPULATION_FORECAST_URL,
        "data": VANTAA_POPULATION_FORECAST,
        "municipality": Municipality.objects.get(name="Vantaa"),
    },
}


class Command(BaseCommand):
    help = "Update statistical districts"

    def handle(self, *args, **options) -> None:
        self.update_population_by_age()
        self.update_population_forecast()

    def update_population_by_age(self):
        start_time = time()
        num_statistics_updated = 0
        for config in population_by_age_configs:
            response = requests.post(
                population_by_age_configs[config]["url"],
                json=population_by_age_configs[config]["data"],
                timeout=120,
            )
            assert response.status_code == 200, "response status code {}".format(
                response.status_code
            )
            result = json.loads(response.text)
            for item in result.get("data"):
                district_id, lang, gender, age, year = item.get("key")
                statistic_key = "%s_population_by_age" % year
                value = item.get("values")[0]
                num_statistics_updated = self._update_statistical_district(
                    age,
                    district_id,
                    num_statistics_updated,
                    statistic_key,
                    value,
                    population_by_age_configs[config]["municipality"],
                )
        logger.info(
            f"{num_statistics_updated} statistic items updated "
            f"in {time() - start_time:.0f} seconds."
        )

    def update_population_forecast(self):
        start_time = time()
        num_statistics_updated = 0
        for config in population_forecast_configs:
            response = requests.post(
                population_forecast_configs[config]["url"],
                json=population_forecast_configs[config]["data"],
                timeout=120,
            )
            assert response.status_code == 200, "response status code {}".format(
                response.status_code
            )
            result = json.loads(response.text)
            for item in result.get("data"):
                lang, district_id, age, origin_key, year = item.get("key")
                statistic_key = "%s_population_forecast" % year
                value = item.get("values")[0]
                num_statistics_updated = self._update_statistical_district(
                    age,
                    district_id,
                    num_statistics_updated,
                    statistic_key,
                    value,
                    population_by_age_configs[config]["municipality"],
                )
        logger.info(
            f"{num_statistics_updated} statistic items updated "
            f"in {time() - start_time:.0f} seconds."
        )

    def _update_statistical_district(
        self,
        age,
        district_id,
        num_statistics_updated,
        statistic_key,
        value,
        municipality,
    ):
        ocd_id = OCD_ID_STATISTICS_BASE + district_id
        division_qs = AdministrativeDivision.objects.filter(ocd_id=ocd_id)
        if division_qs:
            division = division_qs.first()
        else:
            return num_statistics_updated
        if not division.extra:
            division.extra = {}
        if not division.extra.get("statistical_data"):
            division.extra.update({"statistical_data": {}})
        if not division.extra.get("statistical_data").get(statistic_key):
            division.extra.get("statistical_data").update({statistic_key: {}})
        division.extra.get("statistical_data").get(statistic_key).update(
            {
                age: {
                    "value": value if value != ".." else "",
                }
            }
        )
        division.municipality = municipality
        division.save()
        num_statistics_updated += 1
        logger.info(
            "Division {} extra updated to: {}".format(division.id, division.extra)
        )
        return num_statistics_updated
