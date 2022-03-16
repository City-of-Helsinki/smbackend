import re
from datetime import datetime

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import Point
from django.db.utils import IntegrityError
from munigeo.models import Address, Municipality, Street

from smbackend_turku.importers.utils import get_municipality

SOURCE_DATA_SRID = 3877
SOURCE_DATA_URL = (
    f"{settings.TURKU_WFS_URL}"
    "?service=WFS&request=GetFeature&typeName=GIS:Osoitteet&outputFormat=GML3&maxFeatures=80000"
)
# NOTE "django.contrib.gis ERROR: GDAL_ERROR 1: b"Value 'UNKNOWN FIELD 'AddAddress.AddressNumberInt''
# of field Osoitteet.Osoitenumero_luku parsed incompletely to integer 0." Is caused by faulty source data.

# Municipalities in Turku WFS server
MUNICIPALITIES = {
    202: ("Kaarina", "S:t Karins"),
    853: ("Turku", "Åbo"),
}


class AddressImporter:
    def __init__(self, logger=None, layer=None):
        self.logger = logger
        if not layer:
            ds = DataSource(SOURCE_DATA_URL)
            self.layer = ds[0]
        else:
            self.layer = layer

    def get_number_and_letter(self, number_letter):
        number = re.split(r"[a-zA-Z]+", number_letter)[0]
        letter = re.split(r"[0-9]+", number_letter)[-1]
        return number, letter

    def import_addresses(self):
        start_time = datetime.now()

        for muni in MUNICIPALITIES.items():
            municipality = get_municipality(muni[1][0])
            Street.objects.filter(municipality_id=municipality).delete()

        num_incomplete = 0
        num_duplicates = 0
        entries_created = 0
        for feature in self.layer:
            name_fi = feature["Osoite_suomeksi"].as_string()
            name_sv = feature["Osoite_ruotsiksi"].as_string()
            # Add to entry when munigeo supports zip_code
            # zip_code = feature["Postinumero"].as_string()
            if not name_sv:
                name_sv = name_fi
            municipality_num = feature["Kuntanumero"].as_int()
            geometry = feature.geom
            point = Point(geometry.x, geometry.y, srid=SOURCE_DATA_SRID)
            number_letter = feature["Osoitenumero"].as_string()
            # The source data may contain empty entries and they are discarded.
            if not name_fi or not municipality_num or not geometry:
                num_incomplete += 1
                continue

            number = None
            number_end = None
            letter = None
            if number_letter:
                # for number_letter of type "1-4" or "1-4b"
                if re.search(r"-", number_letter):
                    tmp = number_letter.split("-")
                    number = tmp[0]
                    # If number_end contains a letter. e.g. "1-4b"
                    if re.search(r"[a-zA-Z]+", tmp[1]):
                        number_end, letter = self.get_number_and_letter(tmp[1])
                    else:
                        number_end = tmp[1]
                # number_letter of type "1b" or "123b"
                elif re.search(r"[a-zA-Z]+", number_letter):
                    number, letter = self.get_number_and_letter(number_letter)
                # Only a number e.g. "42"
                else:
                    number = number_letter
            try:
                municipality = Municipality.objects.get(
                    id=MUNICIPALITIES[municipality_num][0].lower()
                )
            except KeyError:
                self.logger.warning(
                    f"Municipality number {municipality_num} not found, discarding."
                )
                num_incomplete += 1
                continue

            entry = {}
            entry["street"] = {}
            entry["street"]["name_fi"] = name_fi
            entry["street"]["name_en"] = name_fi
            entry["street"]["municipality"] = municipality

            # The source data may have street names with wrong/conflicting swedish translations
            # to avoid setting these to the db we must check the existens before getting and
            # if not exists we set the swedish name to the entry before creating.
            if Street.objects.filter(**entry["street"]).exists():
                street = Street.objects.get(**entry["street"])
                if street.name_sv != name_sv:
                    self.logger.warning(
                        f"Found street name with wrong/conflicting swedish translation fi: {name_fi} sv: {name_sv}"
                    )

            else:
                entry["street"]["name_sv"] = name_sv
                street = Street.objects.create(**entry["street"])

            # Create full_name that will be used when populating search_column.
            full_name_fi = f"{name_fi} {number_letter}"
            full_name_sv = f"{name_sv} {number_letter}"
            entry["address"] = {}
            entry["address"]["street"] = street
            entry["address"]["location"] = point
            entry["address"]["full_name_fi"] = full_name_fi
            entry["address"]["full_name_sv"] = full_name_sv
            entry["address"]["full_name_en"] = full_name_fi

            if number:
                entry["address"]["number"] = number
            if number_end:
                entry["address"]["number_end"] = number_end
            if letter:
                entry["address"]["letter"] = letter

            try:
                Address.objects.get_or_create(**entry["address"])
            except IntegrityError:
                # Duplicate address causes Integrity error as the unique constraints fails.
                # and they are discarded thus they would confuse when e.g. searching for
                # addresses.
                num_duplicates += 1

            entries_created += 1
            if entries_created % 1000 == 0:
                self.logger.info(
                    "Imported: {}/{}".format(entries_created, len(self.layer))
                )

        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info(
            "Imported {} streets and {} anddresses in {}".format(
                Street.objects.all().count(), Address.objects.all().count(), duration
            )
        )
        self.logger.info("Discarded {} duplicates.".format(num_duplicates))
        self.logger.info("Discarded {} incomplete.".format(num_incomplete))
        self.logger.info(
            "Saving addresses and streets to database, this might take a while..."
        )


def import_addresses(**kwargs):
    importer = AddressImporter(**kwargs)
    return importer.import_addresses()
