import os, sys, django

sys.path.append("/home/juuso/repos/turku/smbackend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smbackend.settings")
django.setup()

from datetime import datetime
import logging
# TODO add to requirements
import aiohttp
import requests
import asyncio
import json
from django.contrib.gis.geos import Point

from munigeo.models import Address, Municipality, Street

SOURCE_DATA_SRID = 4326
TARGET_DATA_SRID = 3067
PAGE_SIZE = 1000
BBOX="20.3775305,59.4756413,23.9205492,61.133482"
URL= f"http://127.0.0.1:8000/v1/address/"



def get_count():
    try:
        response = requests.get(f"{URL}?bbox={BBOX}")        
        count = response.json()["count"]
    except Exception as e:
        raise Exception("Could not fetch count")
    return count



async def main():
    params = {"bbox": BBOX, "page_size": str(PAGE_SIZE)}
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, params=params) as response:
            print("Status:", response.status)
            breakpoint()
            data = await response.read()
            json_response = json.loads(data)
            results = json_response.get('results', None)
      
            print(len(results))


def save_page(results):
    # NOTE this will changen in newest geo-search
    streets_dict = {}

    streets = []
    addresses = []
    for result in results:
        municipality_id = results[0]["street"]["municipality"]["name"]["fi"].lower()
        try:
            municipality = Municipality.objects.get(id=municipality_id)
        except Municipality.DoesNotExist:
            print("Does not exist", municipality)
            continue
        
        name_fi = result["street"]["name"]["fi"]
        name_sv = result["street"]["name"]["sv"] 
        name_en = name_fi
        # if not name_sv:
        #     name_sv = name_fi 
        #street = {"name": {}}
        street = {}
        street["name_fi"] = name_fi
        street["name_sv"] = name_sv 
        street["name_en"] = name_en      
        
       
        # street["municipality"] = municipality 
        # if Street.objects.filter(**street).exists():
        #     street_obj = Street.objects.get(**street)
        #     # if street.name_sv != name_sv:
        #     #     self.logger.warning(
        #     #         f"Found street name with wrong/conflicting swedish translation fi: {name_fi} sv: {name_sv}"
        #     #     )

        # else:                
        #     street_obj = Street.objects.create(**street)
        
        
        
        # street = Street(name=name_fi, name_sv=name_sv, name_en=name_en, municipality=municipality)
        # if street not in streets_dict:
        #     print("add streeet ", steet )
        #     streets_dict.append(street)
        if name_fi not in streets_dict:
            try:  
                obj = Street.objects.get(name=name_fi, name_sv=name_sv, municipality=municipality)
                streets_dict[name_fi] = obj
            except Street.DoesNotExist:
                obj = Street(name=name_fi, name_sv=name_sv, name_en=name_en, municipality=municipality)
                streets_dict[name_fi]  = obj
                streets.append(obj)
        number = result["number"]
        number_end = result["number_end"]
        letter = result["letter"]
        x = result["location"]["coordinates"][0]
        y = result["location"]["coordinates"][1]
        location = Point(x, y, srid=SOURCE_DATA_SRID)
        location.transform(TARGET_DATA_SRID)
        address = Address(street=streets_dict[name_fi], number=number, number_end=number_end, letter=letter,location=location)
        addresses.append(address) 
    
    print(streets)
    Street.objects.bulk_create(streets)
    Address.objects.bulk_create(addresses,ignore_conflicts=True)
    
    #breakpoint()


def fetch_page(page):
    url = f"{URL}?bbox={BBOX}&page_size={PAGE_SIZE}&page={page}"
    #print(url)
    response = requests.get(url)
    results = response.json()["results"]
    print(len(results))
    return results

async def process_page(session, url):
    async with session.get(url) as response:
        data = await response.read()
        json_response = json.loads(data)
        results = json_response.get('results', None)
        breakpoint()
        save_page(results)

async def main(num_pages):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(1, num_pages):
            url = f"{URL}?bbox={BBOX}&page_size={PAGE_SIZE}&page={page}"
            tasks.append(process_page(session, url))
        try:
            res = await asyncio.gather(*tasks)
            return res
        except Exception as e:
            print(e)
            await asyncio.sleep(1)

if __name__ == "__main__":
    start_time = datetime.now()
    Address.objects.all().delete()
    Street.objects.all().delete()
    count = get_count()
    print(get_count())
    count = 100000
    max_page = int(count / PAGE_SIZE) + 1
    print(max_page)
    for page in range(1, max_page, 1):
        results = fetch_page(page)
        save_page(results)
        print(page)
    # loop = asyncio.new_event_loop()
    # loop.run_until_complete(main(num_pages=max_page))

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Fetched {count} in {duration}")
