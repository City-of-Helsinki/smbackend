import csv
import os

from django.conf import settings
from django.contrib.gis.geos import Point

import logging
import re
from datetime import datetime
from django.db.utils import IntegrityError
from django.contrib.gis.gdal import DataSource
from munigeo.models import Address, get_default_srid, Municipality, Street

# As munigeos get_default_srid function returns wrong srid,
#  use srid 3877 instead which is the correct srid.
SOURCE_DATA_SRID = 3877
URL="https://opaskartta.turku.fi/TeklaOGCWeb/WFS.ashx?service=WFS&request=GetFeature&typeName=GIS:Osoitteet&outputFormat=GML3&maxFeatures=80000"
MUNICIPALITIES = {  
    # VARISNAIS-SUOMI
    19: ("Aura", "Aura"),
    202: ("Kaarina", "S:t Karins"),
    322: ("Kemiö", "Kimito"),
    284: ("Koski Tl", "Koskis"),
    304: ("Kustaavi", "Gustavs"),
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
    573: ("Parainen", "Pargas"),
    577: ("Paimio", "Pemar"),
    631: ("Pyhäranta", "Pyhäranta"),
    636: ("Pöytyä", "Pöytis"),
    680: ("Raisio", "Reso"),
    704: ("Rusko", "Rusko"),
    734: ("Salo", "Salo"), 
    738: ("Sauvo", "Sagu"),
    761: ("Somero", "Somero"),
    833: ("Taivassalo", "Tövsala"),
    853: ("Turku", "Åbo"),
    895: ("Uusikaupunki", "Nystad"),
    918: ("Vehmaa", "Vemo"),
}


class AddressImporter:
    
    def __init__(self, logger):
        self.logger = logging.getLogger("search")
        #self.logger.setLevel(logging.INFO)

    def get_number_and_letter(self, number_letter):
        number = re.split(r"[a-zA-Z]+", number_letter)[0]
        letter = re.split(r"[0-9]+", number_letter)[-1]                        
        return number, letter       
  
    def import_addresses(self):
        start_time = datetime.now()
        self.logger.info("Importing addresses.")
        Street.objects.all().delete()
        Address.objects.all().delete()
        ds = DataSource(URL)
        layer = ds[0]
       
        num_incomplete = 0
        num_duplicates = 0
        entries_created = 0
        for feature in layer:
            name_fi = feature["Osoite_suomeksi"].as_string()
            name_sv = feature["Osoite_ruotsiksi"].as_string()
            municipality_num = feature["Kuntanumero"].as_int() 
            geometry = feature.geom
            point = Point(geometry.x, geometry.y, srid=SOURCE_DATA_SRID)
            number_letter = feature["Osoitenumero"].as_string()
            if not name_fi or not municipality_num or not geometry:
                num_incomplete += 1                
                continue
           
            number = None
            number_end = None
            letter = None
            if number_letter:
                if re.search("-", number_letter):
                    tmp = number_letter.split("-")
                    number = tmp[0]
                    if re.search(r"[a-zA-Z]+", tmp[1]):
                        number_end, letter = self.get_number_and_letter(tmp[1])                 
                    else:
                        number_end = tmp[1]                        
                elif re.search(r"[a-zA-Z]+", number_letter):
                    number, letter = self.get_number_and_letter(number_letter)                 
                else:
                    number = number_letter
          #      print("name_fi: ", name_fi, " number: ", number, " end: ", number_end, " letter:", letter)
            
            municipality = Municipality.objects.get(id=MUNICIPALITIES[municipality_num][0].lower())
            
            entry = {}
            entry["street"] = {}
            entry["street"]["name_fi"]=name_fi
            #entry["street"]["name_sv"]=name_sv
            entry["street"]["municipality"]=municipality            
            if Street.objects.filter(**entry["street"]).exists():
                street = Street.objects.get(**entry["street"])
                # There are cases where the name_sv is wrong in the input data.
                if street.name_sv != name_sv:
                    print("Street exists: ", entry["street"])
                    print("different names")
            else:
                entry["street"]["name_sv"]=name_sv
                street = Street.objects.create(**entry["street"])          
            
            # Create full name that will be used when creating search_columns
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
            except IntegrityError as e:
                # Duplicate address causes Integrity error as the unique constraints fails
                num_duplicates += 1
              
            entries_created += 1
            if entries_created % 1000 == 0:
                self.logger.info("{}/{}".format(entries_created, len(layer)))

        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info("Imported {} streets and {} anddresses in {}".format(
            Street.objects.all().count(), Address.objects.all().count(), duration
        ))
        self.logger.info("Discarder {} duplicates.".format(num_duplicates))
        self.logger.info("Discarder {} incomplete.".format(num_incomplete))

        
        

class AddressImporterOLD:
    def __init__(self, logger):
        self.logger = logger

        if hasattr(settings, "PROJECT_ROOT"):
            root_dir = settings.PROJECT_ROOT
        else:
            root_dir = settings.BASE_DIR
        self.data_path = os.path.join(root_dir, "data")

        self.csv_field_names = ("municipality", "street", "street_number", "y", "x")
        self.valid_municipalities = ["turku", "åbo"]

    def _import_address(self, entry):
        street, _ = Street.objects.get_or_create(**entry["street"])
        location = Point(srid=SOURCE_DATA_SRID, **entry["point"])

        Address.objects.get_or_create(
            street=street, defaults={"location": location}, **entry["address"]
        )

    def _create_address_mapping(self, address_reader):
        turku = Municipality.objects.get(id="turku")
        multi_lingual_addresses = {}
        for row in address_reader:
            if row["municipality"].lower() not in self.valid_municipalities:
                continue

            coordinates = row["y"] + row["x"]
            if coordinates not in multi_lingual_addresses:
                # Create a point with a srid, so the coordinates are stored correctly.
                point = Point(float(row["x"]), float(row["y"]), srid=SOURCE_DATA_SRID)
                multi_lingual_addresses[coordinates] = {
                    "street": {"municipality": turku},
                    "point": {"x": point.x, "y": point.y},
                    "address": {"number": row["street_number"]},
                }
            full_name = f"{row['street']} {row['street_number']}"
            if row["municipality"].lower() == "turku":
                multi_lingual_addresses[coordinates]["street"]["name_fi"] = row[
                    "street"
                ]
                multi_lingual_addresses[coordinates]["address"][
                    "full_name_fi"
                ] = full_name

            elif row["municipality"].lower() == "åbo":
                # If we don't have a Finnish name for the street, use the Swedish name
                # for the Finnish street name as well since that is most likely an
                # expected value. If there is a Finnish name for the coordinates lower
                # down in the coordinate list then the Finnish name will be overridden.
                if "name_fi" not in multi_lingual_addresses[coordinates]["street"]:
                    multi_lingual_addresses[coordinates]["street"]["name_fi"] = row[
                        "street"
                    ]
                multi_lingual_addresses[coordinates]["street"]["name_sv"] = row[
                    "street"
                ]
                multi_lingual_addresses[coordinates]["address"][
                    "full_name_sv"
                ] = full_name

        return multi_lingual_addresses

    def import_addresses(self):
        file_path = os.path.join(self.data_path, "turku_addresses.csv")
        print("file", file_path)
        entries_created = 0

        Street.objects.all().delete()
        Address.objects.all().delete()

        with open(file_path, encoding="latin-1") as csvfile:
            address_reader = csv.DictReader(
                csvfile, delimiter=";", fieldnames=self.csv_field_names
            )
            multi_lingual_addresses = self._create_address_mapping(address_reader)

            for entry in multi_lingual_addresses.values():
                self._import_address(entry)

                entries_created += 1
                if entries_created % 1000 == 0:
                    self.logger.debug(
                        "row {} / {}".format(
                            entries_created, len(multi_lingual_addresses.values())
                        )
                    )

        self.logger.debug("Added {} addresses".format(entries_created))


def import_addresses(**kwargs):
   
    importer = AddressImporter(**kwargs)
   
    return importer.import_addresses()
