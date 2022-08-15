"""
This management command updates statistical district extra-data from Statistics Finland
"""
import json
import logging
import os
from time import time

import requests
from django.core.management.base import BaseCommand
from munigeo.models import AdministrativeDivision

logger = logging.getLogger("import")

OCD_ID_STATISTICS_BASE = "ocd-division/country:fi/tilastoalue:"


def get_abs_file_path(json_file):
    script_dir = os.path.dirname(__file__)
    rel_path = "statistical_queries/" + json_file
    return os.path.join(script_dir, rel_path)


HELSINKI_QUERY_BY_AGE_ALL_URL = (
    "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaerak/pksoa/A01S_HKI_Vakiluku.px"
)
with open(get_abs_file_path("helsinki_query_by_age_all.json")) as f:
    HELSINKI_QUERY_BY_AGE_ALL = json.load(f)

ESPOO_QUERY_BY_AGE_ALL_URL = (
    "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaerak/pksoa/B01S_ESP_Vakiluku.px"
)
with open(get_abs_file_path("espoo_query_by_age_all.json")) as f:
    ESPOO_QUERY_BY_AGE_ALL = json.load(f)

VANTAA_QUERY_BY_AGE_ALL_URL = (
    "https://stat.hel.fi:443/api/v1/fi/Aluesarjat/vrm/vaerak/pksoa/C01S_VAN_Vakiluku.px"
)
with open(get_abs_file_path("vantaa_query_by_age_all.json")) as f:
    VANTAA_QUERY_BY_AGE_ALL = json.load(f)

queries = {
    HELSINKI_QUERY_BY_AGE_ALL_URL: HELSINKI_QUERY_BY_AGE_ALL,
    ESPOO_QUERY_BY_AGE_ALL_URL: ESPOO_QUERY_BY_AGE_ALL,
    VANTAA_QUERY_BY_AGE_ALL_URL: VANTAA_QUERY_BY_AGE_ALL,
}


class Command(BaseCommand):
    help = "Update statistical districts"

    def handle(self, *args, **options) -> None:
        start_time = time()
        num_statistics_updated = 0
        for query in queries:
            response = requests.post(query, json=queries[query], timeout=120)
            assert response.status_code == 200, "response status code {}".format(
                response.status_code
            )
            result = json.loads(response.text)
            for item in result.get("data"):
                district_id, lang, gender, age, year = item.get("key")
                value = item.get("values")[0]
                ocd_id = OCD_ID_STATISTICS_BASE + district_id
                division_qs = AdministrativeDivision.objects.filter(ocd_id=ocd_id)
                if division_qs:
                    division = division_qs.first()
                else:
                    continue
                if not division.extra:
                    division.extra = {}
                    division.extra.update({"statistical_data": {year: {}}})
                division.extra.get("statistical_data").get(year).update(
                    {
                        age: {
                            "value": value,
                        }
                    }
                )
                division.save()
                num_statistics_updated += 1
                logger.info(
                    "Division {} extra updated to: {}".format(
                        division.id, division.extra
                    )
                )

        logger.info(
            f"{num_statistics_updated} statistic items updated "
            f"in {time() - start_time:.0f} seconds."
        )
