from datetime import datetime
from queue import Empty, Queue
from threading import Thread

import requests
import urllib3
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import Point
from django.db import transaction
from munigeo.models import Address, PostalCodeArea, Street
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from smbackend_turku.importers.utils import get_municipality

SOURCE_DATA_SRID = 4326
TARGET_DATA_SRID = 3067
SOURCE_SRS = SpatialReference(SOURCE_DATA_SRID)
TARGET_SRS = SpatialReference(TARGET_DATA_SRID)
PAGE_SIZE = 1000
# Determines how many threads are run simultaneously when importing addresses
THREAD_POOL_SIZE = 2
BASE_URL = settings.GEO_SEARCH_LOCATION

# Contains the municipalities to import
# Note, # 202: ("Kaarina", "S:t Karins"), and  # 853: ("Turku", "Åbo"),
# are Removed thus they are imported from the address importer
MUNICIPALITIES = {
    19: ("Aura", "Aura"),
    284: ("Koski Tl", "Koskis"),
    304: ("Kustavi", "Gustavs"),
    322: ("Kemiönsaari", "Kimitoön"),
    400: ("Laitila", "Letala"),
    423: ("Lieto", "Lundo"),
    430: ("Loimaa", "Loimaa"),
    445: ("Parainen", "Pargas"),
    480: ("Marttila", "S:t Mårtens"),
    481: ("Masku", "Masko"),
    503: ("Mynämäki", "Virmo"),
    529: ("Naantali", "Nådendal"),
    538: ("Nousiainen", "Nousis"),
    561: ("Oripää", "Oripää"),
    577: ("Paimio", "Pemar"),
    631: ("Pyhäranta", "Pyhäranta"),
    636: ("Pöytyä", "Pöytis"),
    680: ("Raisio", "Reso"),
    704: ("Rusko", "Rusko"),
    734: ("Salo", "Salo"),
    738: ("Sauvo", "Sagu"),
    761: ("Somero", "Somero"),
    833: ("Taivassalo", "Tövsala"),
    895: ("Uusikaupunki", "Nystad"),
    918: ("Vehmaa", "Vemo"),
}
# Contains the municipalities to enrich. The municipalites are the ones that
# comes from the WFS importer(addresses.py)
ENRICH_MUNICIPALITIES = {
    202: ("Kaarina", "S:t Karins"),
    853: ("Turku", "Åbo"),
}


class GeoSearchImporter:
    addresses_imported = 0
    streets_imported = 0
    streets_enriched_with_swedish_translation = 0
    postal_code_areas_enriched = 0
    postal_code_areas_added_to_addresses = 0
    postal_code_areas_created = 0
    duplicate_addresses = 0
    coord_transform = CoordTransform(SOURCE_SRS, TARGET_SRS)

    # Contains the streets of the current municipality, used for caching
    streets_cache = {}
    # Contains the addresses of the current municipality, as the source contains
    # duplicates, the address_cache is used to lookup if the address is already saved.
    address_cache = {}
    postal_code_areas_cache = {}
    # The import source may fail, create import_strategy
    retry_strategy = Retry(
        total=10,
        status_forcelist=[400, 408, 429, 500, 502, 503, 504],
        method_whitelist=[
            "GET",
        ],
        backoff_factor=40,  # 20, 40, 80 , 160, 320, 640, 1280...seconds
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    def __init__(self, logger=None):
        self.logger = logger

    def get_count(self, url):
        headers = {"Authorization": f"Bearer Api-Key {settings.GEO_SEARCH_API_KEY}"}
        try:
            response = self.http.get(url, headers=headers)
        except urllib3.exceptions.MaxRetryError as ex:
            self.logger.error(ex)

        count = response.json()["count"]
        return count

    def fetch_page(self, url, page):
        request_url = f"{url}&page={page}"
        headers = {"Authorization": f"Bearer Api-Key {settings.GEO_SEARCH_API_KEY}"}
        try:
            response = self.http.get(request_url, headers=headers)
        except urllib3.exceptions.MaxRetryError as ex:
            self.logger.error(ex)

        results = response.json()["results"]
        self.logger.info(
            f"Fetched page {page} from {request_url} with {len(results)} items."
        )
        return results

    def worker(self, page_queue, results_queue, url):
        while not page_queue.empty():
            try:
                page = page_queue.get_nowait()
            except Empty:
                break
            try:
                results = self.fetch_page(url, page)
            except Exception as err:
                results_queue.put(err)
            else:
                results_queue.put(results)
            finally:
                page_queue.task_done()

    def get_multilingual_street_names(self, result):
        street_name_fi = result["street"]["name"]["fi"]
        street_name_sv = result["street"]["name"]["sv"]
        # Assign Finnish name to English name, so when searching addresses in English
        # it gives results.
        street_name_en = street_name_fi
        if not street_name_sv:
            street_name_sv = street_name_fi
        return street_name_fi, street_name_sv, street_name_en

    def get_multilingual_full_names(
        self, street_name_fi, street_name_sv, street_name_en, number, number_end, letter
    ):
        """
        Return the multilingual full names used to populate the search columns
        """
        full_name_fi = street_name_fi
        full_name_sv = street_name_sv
        full_name_en = street_name_en
        if number:
            full_name_fi += f" {number}"
            full_name_sv += f" {number}"
            full_name_en += f" {number}"
        if number_end:
            full_name_fi += f"-{number}"
            full_name_sv += f"-{number}"
            full_name_en += f"-{number}"
        if letter:
            full_name_fi += letter
            full_name_sv += letter
            full_name_en += letter
        return full_name_fi, full_name_sv, full_name_en

    def get_location(self, result):
        lat = None
        lon = None
        try:
            lat = result["location"]["coordinates"][0]
            lon = result["location"]["coordinates"][1]
        except KeyError:
            return None
        location = Point(lat, lon, srid=SOURCE_DATA_SRID)
        location.transform(self.coord_transform)
        return location

    def get_or_create_postal_code_area(self, postal_code, result):
        postal_code_area, created = PostalCodeArea.objects.get_or_create(
            postal_code=postal_code
        )
        if created:
            self.postal_code_areas_created += 1
        name_added = False
        if not postal_code_area.name_fi:
            postal_code_area.name_fi = result["postal_code_area"]["name"]["fi"]
            name_added = True
        if not postal_code_area.name_sv:
            postal_code_area.name_sv = result["postal_code_area"]["name"]["sv"]
            name_added = True
        if name_added:
            self.postal_code_areas_enriched + 1
            postal_code_area.save()
        return postal_code_area

    @transaction.atomic
    def save_page(self, results, municipality):
        cache_misses = 0
        cache_hits = 0
        streets = []
        addresses = []
        for result in results:
            postal_code = result["postal_code_area"]["postal_code"]
            if postal_code not in self.postal_code_areas_cache:
                self.postal_code_areas_cache[postal_code] = (
                    self.get_or_create_postal_code_area(postal_code, result)
                )

            (
                street_name_fi,
                street_name_sv,
                street_name_en,
            ) = self.get_multilingual_street_names(result)
            if street_name_fi not in self.streets_cache:
                street_entry = {
                    "name": street_name_fi,
                    "name_sv": street_name_sv,
                    "name_en": street_name_en,
                    "municipality": municipality,
                }
                cache_misses += 1
                try:
                    street = Street.objects.get(**street_entry)
                except Street.DoesNotExist:
                    street = Street(**street_entry)
                    streets.append(street)

                self.streets_cache[street_name_fi] = street
            else:
                cache_hits += 1

            location = self.get_location(result)
            if not location:
                continue
            number = result.get("number", "")
            number_end = result.get("number_end", "")
            letter = result.get("letter", "")
            full_name_fi, full_name_sv, full_name_en = self.get_multilingual_full_names(
                street_name_fi,
                street_name_sv,
                street_name_en,
                number,
                number_end,
                letter,
            )

            # Ensures that no duplicates goes to DB, as there are some in the source data
            if full_name_fi not in self.address_cache:
                address = Address(
                    municipality_id=municipality.id,
                    street=self.streets_cache[street_name_fi],
                    number=number,
                    number_end=number_end,
                    letter=letter,
                    location=location,
                    postal_code_area=self.postal_code_areas_cache[postal_code],
                    full_name_fi=full_name_fi,
                    full_name_sv=full_name_sv,
                    full_name_en=full_name_en,
                )
                addresses.append(address)
                self.address_cache[full_name_fi] = address
            else:
                self.duplicate_addresses += 1
        len_streets = len(streets)
        len_addresses = len(addresses)
        if len_streets > 0:
            Street.objects.bulk_create(streets)
        Address.objects.bulk_create(addresses)

        self.logger.info(
            f"Page saved with {len_addresses} addresses and {len_streets} street."
        )
        self.logger.info(
            f"Page processed with {cache_hits} caches hits and {cache_misses} misses."
        )
        self.addresses_imported += len_addresses
        self.streets_imported += len_streets

    def import_municipality(self, municipality, municipality_code):
        # contains the page numbers to fetch
        page_queue = Queue()
        # contains the results fetched
        results_queue = Queue()
        self.streets_cache = {}
        self.address_cache = {}
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={1}"

        count = self.get_count(url)
        max_page = int(count / PAGE_SIZE) + 1
        self.logger.info(f"Fetching municipality: {municipality}")
        self.logger.info(
            f"Source data for municipality contains {count} items and {max_page} pages(page_size={PAGE_SIZE})."
        )

        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={PAGE_SIZE}"
        for pool in range(0, max_page, THREAD_POOL_SIZE):
            threads = []
            # Create threads to the pool
            for page in range(1, THREAD_POOL_SIZE + 1):
                page_number = page + pool
                if page_number <= max_page:
                    page_queue.put(page_number)
                    threads.append(
                        Thread(
                            target=self.worker,
                            args=(page_queue, results_queue, url),
                        )
                    )

            for thread in threads:
                thread.start()
            page_queue.join()
            while threads:
                threads.pop().join()
            while not results_queue.empty():
                results = results_queue.get()
                if not isinstance(results, Exception):
                    self.save_page(results, municipality)
                else:
                    raise results

            end_time = datetime.now()
            duration = end_time - self.start_time
            output_rate = (
                self.streets_imported + self.addresses_imported
            ) / duration.total_seconds()
            self.logger.info(
                f"Duration {duration}, Current (fetching+processing+storing)"
                + f" average rate (addresses&streets/s): {output_rate}"
            )
            self.logger.info(
                f"Addresses imported: {self.addresses_imported}, Streets imported: {self.streets_imported}"
            )

    @transaction.atomic
    def enrich_page(self, results, municipality):
        streets = []
        addresses = []
        for result in results:
            (
                street_name_fi,
                street_name_sv,
                street_name_en,
            ) = self.get_multilingual_street_names(result)

            if result["postal_code_area"] is None:
                self.postal_code_not_found += 1
                continue

            postal_code = result["postal_code_area"]["postal_code"]
            if postal_code not in self.postal_code_areas_cache:
                self.postal_code_areas_cache[postal_code] = (
                    self.get_or_create_postal_code_area(postal_code, result)
                )
            # name_sv is not added as there might be a swedish translation
            street_entry = {
                "name": street_name_fi,
                "name_en": street_name_en,
                "municipality": municipality,
            }
            if street_name_fi not in self.streets_cache:
                try:
                    street = Street.objects.get(**street_entry)
                    # Check if finnish and swedish name are the same(no translation) and
                    #  if translated swedish name exists, then we have a translation
                    if (
                        street.name_fi == street.name_sv
                        and street_name_sv != street.name_sv
                    ):
                        # update the swedish name
                        self.logger.info(
                            f"Updated translation for {street_name_fi} to {street_name_sv}"
                        )
                        Street.objects.filter(**street_entry).update(
                            name_sv=street_name_sv
                        )
                        self.streets_enriched_with_swedish_translation += 1
                    street_entry["name_sv"] = street_name_sv

                except Street.DoesNotExist:
                    street_entry["name_sv"] = street_name_sv
                    street = Street(**street_entry)
                    streets.append(street)
                self.streets_cache[street_name_fi] = street
            else:
                street_entry["name_sv"] = street_name_sv

            address_entry = {
                "municipality_id": municipality.id,
                "street": self.streets_cache[street_name_fi],
                "number": result["number"],
                "number_end": result["number_end"],
                "letter": result["letter"],
            }
            address = None
            try:
                address = Address.objects.get(**address_entry)
                if not address.postal_code_area:
                    address.postal_code_area = self.postal_code_areas_cache[postal_code]
                    self.postal_code_areas_added_to_addresses += 1
                    address.save()
            except Address.DoesNotExist:
                location = self.get_location(result)
                if location:
                    (
                        full_name_fi,
                        full_name_sv,
                        full_name_en,
                    ) = self.get_multilingual_full_names(
                        street_entry["name"],
                        street_entry["name_sv"],
                        street_entry["name_en"],
                        address_entry["number"],
                        address_entry["number_end"],
                        address_entry["letter"],
                    )
                    address_entry["full_name_fi"] = full_name_fi
                    address_entry["full_name_sv"] = full_name_sv
                    address_entry["full_name_en"] = full_name_en
                    address_entry["location"] = location
                    address_entry["postal_code_area"] = self.postal_code_areas_cache[
                        postal_code
                    ]
                    address = Address(**address_entry)
                    # Ensures that no duplicates goes to DB, as there are some in the source data
                    if full_name_fi not in self.address_cache:
                        addresses.append(address)
                        self.address_cache[full_name_fi] = address
                    else:
                        self.duplicate_addresses += 1

        if streets:
            Street.objects.bulk_create(streets)
        if addresses:
            Address.objects.bulk_create(addresses)

        self.logger.info(
            f"Processed page, added {len(streets)} streets and {len(addresses)} addresses."
        )
        self.addresses_imported += len(addresses)
        self.streets_imported += len(streets)

    def enrich_municipality(self, municipality, municipality_code):
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={1}"
        self.streets_cache = {}
        self.address_cache = {}
        count = self.get_count(url)
        max_page = int(count / PAGE_SIZE) + 1
        self.logger.info(f"Enriching municipality {municipality}.")
        self.logger.info(
            f"Source data for municipality contains {count} items and {max_page} pages(page_size={PAGE_SIZE})."
        )
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={PAGE_SIZE}"
        # add 1 as we start from 1 not 0.
        for page in range(1, max_page + 1):
            results = self.fetch_page(url, page)
            self.enrich_page(results, municipality)

    def enrich_addresses(self):
        """
        Enriches municipalities imported from the WFS server with streets, aaddress
        and postal code areas. Also enriches with Swedish street name translations
        if found and names for postal code areas.
        """

        self.logger.info("Enriching existing addresses with geo_search addresses.")
        self.start_time = datetime.now()
        self.postal_code_areas_cache = {}
        self.streets_imported = 0
        self.addresses_imported = 0
        self.duplicate_addresses = 0
        self.postal_code_not_found = 0
        self.postal_code_areas_added_to_addresses = 0
        self.postal_code_areas_created = 0
        for muni in ENRICH_MUNICIPALITIES.items():
            code = muni[0]
            municipality = get_municipality(muni[1][0])
            if not municipality:
                self.logger.warning(f"Municipality {muni[1][0]} not found.")
                continue
            self.enrich_municipality(municipality, code)

        end_time = datetime.now()
        duration = end_time - self.start_time
        self.logger.info(f"Finnished enriching addresses in:{duration}")
        self.logger.info(
            f"Imported {self.streets_imported} streets and {self.addresses_imported} addresses."
        )
        self.logger.info(
            f"Enriched {self.streets_enriched_with_swedish_translation} streets with swedish translaitons."
        )
        self.logger.info(
            f"Enriched {self.postal_code_areas_enriched} postal_code_areas."
        )
        self.logger.info(f"Created {self.postal_code_areas_created} postal_code_areas.")
        self.logger.info(
            f"Added {self.postal_code_areas_added_to_addresses} postal_code_areas to addresses."
        )
        self.logger.info(
            f"Found and ignored {self.duplicate_addresses} duplicate adresses."
        )
        self.logger.info(
            f"Skipped {self.postal_code_not_found} addresses, reason: no postal code."
        )

    def import_addresses(self):
        self.logger.info("Importing addresses from geo-search.")

        self.start_time = datetime.now()
        self.postal_code_areas_cache = {}
        self.postal_code_areas_created = 0

        for muni in MUNICIPALITIES.items():
            code = muni[0]
            municipality = get_municipality(muni[1][0])
            if not municipality:
                self.logger.warning(f"Municipality {muni[1][0]} not found.")
                continue
            # Delete all addresses of the municipality, ensures data is up to date.
            Street.objects.filter(municipality_id=municipality).delete()

            self.import_municipality(municipality, code)

        end_time = datetime.now()
        duration = end_time - self.start_time
        output_rate = self.addresses_imported / duration.total_seconds()
        tot_output_rate = (
            self.streets_imported + self.addresses_imported
        ) / duration.total_seconds()
        self.logger.info(
            f"Importing of addresses from geo_search finnished in: {duration}"
        )
        self.logger.info(
            "Streets and Addresses where (fetched+processed+stored) at a rate of"
            + f"(addresses&streets/s) {tot_output_rate}"
        )
        self.logger.info(
            f"Found and ignored {self.duplicate_addresses} duplicate adresses."
        )
        self.logger.info(f"Created {self.postal_code_areas_created} postal_code_areas.")
        self.logger.info(
            f"Addresses where fetched and stored at a average rate of (addresses/s): {output_rate}"
        )
        self.logger.info(
            f"THREAD_POOL_SIZE: {THREAD_POOL_SIZE} PAGE_SIZE:{PAGE_SIZE}"
            + f" Fetched {self.addresses_imported} addresses and {self.streets_imported} streets."
        )


def import_geo_search_addresses(**kwargs):
    """
    Imports addresses from geo-search.
    """
    importer = GeoSearchImporter(**kwargs)
    return importer.import_addresses()


def import_enriched_addresses(**kwargs):
    """
    Enriches muncipalities streets and addresses with data from geo-search
    """
    importer = GeoSearchImporter(**kwargs)
    return importer.enrich_addresses()
