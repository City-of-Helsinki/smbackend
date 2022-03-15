from datetime import datetime
from queue import Empty, Queue
from threading import Thread

import requests
from django.contrib.gis.geos import Point
from munigeo.models import Address, Street

from smbackend_turku.importers.utils import get_municipality

SOURCE_DATA_SRID = 4326
TARGET_DATA_SRID = 3067
PAGE_SIZE = 20000  # TODO set to 20000
# Determines how many threads are run simultaneously when importing addresses
THREAD_POOL_SIZE = 2
BBOX = "20.3775305,59.4756413,23.9205492,61.133482"
BASE_URL = f"http://127.0.0.1:8000/v1/address/"

# Contains the municipalities to import
MUNICIPALITIES = {
    19: ("Aura", "Aura"),
    # 202: ("Kaarina", "S:t Karins"),
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
    # 853: ("Turku", "Åbo"), # Remove
    895: ("Uusikaupunki", "Nystad"),
    918: ("Vehmaa", "Vemo"),
}
# Contains the municipalities to enrich
# The municipalites are the one that comes from the WFS importer
ENRICH_MUNICIPALITIES = {
    202: ("Kaarina", "S:t Karins"),
    853: ("Turku", "Åbo"),
}


class GeoSearchImporter:
    addresses_imported = 0
    streets_imported = 0
    streets_enriched_with_swedish_translation = 0
    duplicate_addresses = 0
    streets_cache = {}
    address_cache = {}

    def __init__(self, logger=None):
        self.logger = logger

    def get_count(self, url):
        try:
            response = requests.get(url)
            count = response.json()["count"]
        except Exception:
            raise Exception("Could not fetch count")
        return count

    def get_multilingual_street_names(self, result):
        street_name_fi = result["street"]["name"]["fi"]
        street_name_sv = result["street"]["name"]["sv"]
        street_name_en = street_name_fi
        if not street_name_sv:
            street_name_sv = street_name_fi
        return street_name_fi, street_name_sv, street_name_en

    def get_multilingual_full_names(
        self, street_name_fi, street_name_sv, street_name_en, number, number_end, letter
    ):
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
        lat = result["location"]["coordinates"][0]
        lon = result["location"]["coordinates"][1]
        location = Point(lat, lon, srid=SOURCE_DATA_SRID)
        location.transform(TARGET_DATA_SRID)
        return location

    def save_page(self, results, municipality):
        cache_misses = 0
        cache_hits = 0
        streets = []
        addresses = []
        for result in results:
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
            number = result["number"]
            number_end = result["number_end"]
            letter = result["letter"]
            full_name_fi, full_name_sv, full_name_en = self.get_multilingual_full_names(
                street_name_fi,
                street_name_sv,
                street_name_en,
                number,
                number_end,
                letter,
            )
            location = self.get_location(result)
            # Ensures that no duplicates goes to DB, as there are some in the source data
            if full_name_fi not in self.address_cache:
                address = Address(
                    street=self.streets_cache[street_name_fi],
                    number=number,
                    number_end=number_end,
                    letter=letter,
                    location=location,
                    full_name_fi=full_name_fi,
                    full_name_sv=full_name_sv,
                    full_name_en=full_name_en,
                )
                addresses.append(address)
                self.address_cache[full_name_fi] = address
            else:
                self.duplicate_addresses += 1

        print(f"Caches hits: {cache_hits} Misses: {cache_misses}")
        if streets:
            Street.objects.bulk_create(streets)
        # Address.objects.bulk_create(addresses, ignore_conflicts=True)
        Address.objects.bulk_create(addresses)

        self.addresses_imported += len(results)
        self.streets_imported += len(streets)

    def fetch_page(self, url, page):
        request_url = f"{url}&page={page}"
        response = requests.get(request_url)
        results = response.json()["results"]
        print("url:", request_url, " len results:", len(results), " page: ", page)
        return results

    def worker(self, page_queue, results_queue, url):
        while not page_queue.empty():
            try:
                item = page_queue.get_nowait()
            except Empty:
                break
            else:
                results = self.fetch_page(url, item)
                results_queue.put(results)
                page_queue.task_done()

    def import_municipality(self, municipality, municipality_code):
        print(f"Fetching municipality: {municipality_code}")

        page_queue = Queue()
        results_queue = Queue()
        self.streets_cache = {}
        self.address_cache = {}
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={1}"

        count = self.get_count(url)
        max_page = int(count / PAGE_SIZE) + 1
        print("count:", count, "max_page:", max_page)
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={PAGE_SIZE}"

        for pool in range(0, max_page, THREAD_POOL_SIZE):
            threads = []
            # TODO print imported and current rate
            # Create threads to the pool
            for page in range(1, THREAD_POOL_SIZE + 1):
                index = page + pool
                if index <= max_page:
                    page_queue.put(index)  # Todo rename to page_queu
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
                self.save_page(results_queue.get(), municipality)

            end_time = datetime.now()
            duration = end_time - self.start_time
            output_rate = self.addresses_imported / duration.total_seconds()

            print(
                f"Duration {duration}, Current outputrate: {output_rate} Addresses imported: {self.addresses_imported}, Streets imported: {self.streets_imported}"
            )

    def enrich_page(self, results, municipality):
        streets = []
        addresses = []
        for result in results:
            (
                street_name_fi,
                street_name_sv,
                street_name_en,
            ) = self.get_multilingual_street_names(result)
            # Do not add name_sv as there might be a swedish translation
            # if the name_fi and name_sv are equal
            street_entry = {
                "name": street_name_fi,
                "name_en": street_name_en,
                "municipality": municipality,
            }
            if street_name_fi not in self.streets_cache:
                try:
                    street = Street.objects.get(**street_entry)
                    # Check finnish and swedish name are the same(no translation) and
                    #  if translated swedish name exists
                    if (
                        street.name_fi == street.name_sv
                        and street_name_sv != street.name_sv
                    ):
                        # update the swedish name
                        print("Update translation", street_name_fi)
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

            # Do not add location. Locations from WFS are more accurate
            location = self.get_location(result)

            address_entry = {
                "street": self.streets_cache[street_name_fi],
                "number": result["number"],
                "number_end": result["number_end"],
                "letter": result["letter"],
            }
            address = None
            try:
                address = Address.objects.get(**address_entry)
            except Address.DoesNotExist:
                location = self.get_location(result)

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

        if streets or addresses:
            print(f"Added {len(streets)} streets and {len(addresses)} addresses.")
        self.addresses_imported += len(results)
        self.streets_imported += len(streets)

    def enrich_municipality(self, municipality, municipality_code):
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={1}"

        count = self.get_count(url)
        max_page = int(count / PAGE_SIZE) + 1
        print("count:", count, "max_page:", max_page)
        url = f"{BASE_URL}?municipalitycode={municipality_code}&page_size={PAGE_SIZE}"
        # add 1 as we start from 1 not 0.
        for page in range(1, max_page + 1):
            results = self.fetch_page(url, page)
            self.enrich_page(results, municipality)

    def enrich_addresses(self):
        print("Enriching existins addresses with geo_search addresses.")
        self.start_time = datetime.now()
        self.streets_imported = 0
        self.addresses_imported = 0
        self.duplicate_addresses = 0
        for muni in ENRICH_MUNICIPALITIES.items():
            code = muni[0]
            municipality = get_municipality(muni[1][0])
            self.streets_cache = {}
            self.address_cache = {}

            self.enrich_municipality(municipality, code)
        end_time = datetime.now()
        duration = end_time - self.start_time
        output_rate = self.addresses_imported / duration.total_seconds()

        print(f"Finnished enriching addresses in:{duration}")
        print(
            f"Imported {self.streets_imported} streets and {self.addresses_imported} addresses."
        )
        print(
            f"Enriched {self.streets_enriched_with_swedish_translation} streets with swedish translaitons."
        )
        print(f"Found {self.duplicate_addresses} duplicate adresses.")

    def import_addresses(self):
        print("Importing addresses from geo-search")
        for muni in MUNICIPALITIES.items():
            municipality = get_municipality(muni[1][0])
            Street.objects.filter(municipality_id=municipality).delete()

        # start_time = datetime.now()
        self.start_time = datetime.now()

        for muni in MUNICIPALITIES.items():
            code = muni[0]
            municipality = get_municipality(muni[1][0])
            if not municipality:
                print("municipality not found")
                continue
            self.import_municipality(municipality, code)

        end_time = datetime.now()
        duration = end_time - self.start_time
        output_rate = self.addresses_imported / duration.total_seconds()
        print(f"Importing of addresses from geo_search finnished in: {duration}")
        print(f"Addresses where stored at a avarega rate (addresses/s): {output_rate}")
        print(
            f"THREAD_POOL_SIZE: {THREAD_POOL_SIZE} Page size:{PAGE_SIZE} Fetched {self.addresses_imported} addresses and {self.streets_imported} streets."
        )
        print(f"Found {self.duplicate_addresses} in input data on one page")


def import_geo_search_addresses(**kwargs):
    importer = GeoSearchImporter(**kwargs)
    importer.import_addresses()
    importer.enrich_addresses()
    return

"""
Benchmark data

mporting of addresses from geo_search finnished in: 8:55:58.705729
Addresses where stored at a avarega rate (addresses/s): 48.71066681602769
THREAD_POOL_SIZE: 2 Page size:20000 Fetched 1566472 addresses and 15623 streets.


THREAD_POOL_SIZE: 5 Page size:1000 Fetched 54727 in 0:18:04.318211
THREAD_POOL_SIZE: 8 Page size:1000 Fetched 54727 in 0:19:52.579555
THREAD_POOL_SIZE: 4 Page size:2000 Fetched 54727 in 0:17:26.362902
THREAD_POOL_SIZE: 2 Page size:8000 Fetched 54727 in 0:18:31.251561, output_rate(addrs/s): 49.24807480202946
THREAD_POOL_SIZE: 4 Page size:2000 Fetched 1661225 in 8:49:30.547232, output_rate(addrs/s): 52.28820856843087
THREAD_POOL_SIZE: 2 Page size:8000 Fetched 1661225 in 8:17:29.409040, output_rate(addrs/s): 55.65353062011576
THREAD_POOL_SIZE: 2 Page size:20000 Fetched 1661225 in 8:08:49.436471, output_rate(addrs/s): 56.640194967351846
"""
