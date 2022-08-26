import io
import logging
from datetime import timedelta

import pandas as pd
import requests
from django.conf import settings
from django.contrib.gis.gdal import DataSource as DataSource
from django.contrib.gis.geos import GEOSGeometry, Point

from eco_counter.models import ECO_COUNTER, Station, TRAFFIC_COUNTER
from mobility_data.importers.utils import get_root_dir

logger = logging.getLogger("eco_counter")

TRAFFIC_COUNTER_META_DATA_GEOJSON = "meta_data.geojson"

TRAFFIC_COUNTER_BASE_URL = "https://data.turku.fi/"
TRAFFIC_COUNTER_START_YEAR = "2015"
TRAFFIC_COUNTER_START_YEAR_URL = (
    TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2015_laskenta.csv"
)
TRAFFIC_COUNTER_CSV_URLS = {
    "2015": {"url": TRAFFIC_COUNTER_START_YEAR_URL},
    "2016": {
        "url": TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2016_laskenta.csv"
    },
    "2017": {
        "url": TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2017_laskenta.csv"
    },
    "2018": {
        "url": TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2018_laskenta.csv"
    },
    "2019": {
        "url": TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2019_laskenta.csv"
    },
    "2020": {
        "url": TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2020_laskenta.csv"
    },
    "2021": {
        "url": TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2021_laskenta.csv"
    },
    "2022": {
        "url": TRAFFIC_COUNTER_BASE_URL + "2yxpk2imqi2mzxpa6e6knq/2022_laskenta.csv"
    },
}


def get_traffic_counter_meta_data_data_layer():
    meta_file = f"{get_root_dir()}/eco_counter/data/{TRAFFIC_COUNTER_META_DATA_GEOJSON}"
    return DataSource(meta_file)[0]


def get_dataframe(url):
    response = requests.get(url)
    assert (
        response.status_code == 200
    ), "Fetching observations csv {} status code: {}".format(url, response.status_code)
    string_data = response.content
    csv_data = pd.read_csv(io.StringIO(string_data.decode("utf-8")))
    return csv_data


def get_eco_counter_csv():
    return get_dataframe(settings.ECO_COUNTER_OBSERVATIONS_URL)


def get_traffic_counter_csv():
    df = get_dataframe(TRAFFIC_COUNTER_START_YEAR_URL)
    # Append all the Traffic counter CSV data into one CSV.
    for key in TRAFFIC_COUNTER_CSV_URLS.keys():
        # Skip start year as it is in the initial dataframe
        if key in TRAFFIC_COUNTER_START_YEAR:
            continue
        app_df = get_dataframe(TRAFFIC_COUNTER_CSV_URLS[key]["url"])
        # TODO fix deprecated append
        df = df.append(app_df)
    data_layer = get_traffic_counter_meta_data_data_layer()
    ids_not_found = 0
    # Rename columns to format name_type|direction
    # e.g. Yliopistonkatu AK
    for feature in data_layer:
        id = feature["Mittauspisteiden_ID"].as_int()
        direction = feature["Suunta"].as_string()
        direction = "K"
        measurement_type = feature["Tyyppi"].as_string()
        # with the id find the col  from csv
        name = feature["Osoite_fi"].as_string()
        regex = rf".*\({id}\)"
        column = df.filter(regex=regex)
        if len(column.keys()) > 1:
            # do some error handling
            pass
        if len(column.keys()) == 0:
            logger.warning(f"ID:{id} not found in the csv data")
            ids_not_found += 1
            continue
        col_name = column.keys()[0]
        # new_name = f"{addr_fi}_{id} {measurement_type}{direction}"
        new_name = f"{name} {measurement_type}{direction}"
        # Rename the column
        df.columns = df.columns.str.replace(col_name, new_name, regex=False)
    # drop columns with number, i.e. not in metadata as the new column
    # name are in format name_type|direction and does not contain numbers
    df = df.drop(df.filter(regex="[0-9]+").columns, axis=1)
    print(len(df.columns))
    # Combine columns with same name, i.e. combines lanes into one.
    df = df.groupby(df.columns, axis=1).sum()
    print(len(df.columns))
    logger.info(df.info(verbose=False))
    # Move column 'startTime to first (0) position.
    df.insert(0, "startTime", df.pop("startTime"))
    # df.to_csv("out.csv")
    return df


def save_traffic_counter_stations():

    saved = 0
    data_layer = get_traffic_counter_meta_data_data_layer()
    for feature in data_layer:
        name = feature["Osoite_fi"].as_string()
        name_sv = feature["Osoite_sv"].as_string()
        name_en = feature["Osoite_en"].as_string()
        if Station.objects.filter(name=name).exists():
            continue

        station = Station()
        station.name = name
        station.name_sv = name_sv
        station.name_en = name_en
        station.csv_data_source = TRAFFIC_COUNTER
        geom = GEOSGeometry(feature.geom.wkt, srid=feature.geom.srid)
        geom.transform(settings.DEFAULT_SRID)
        station.geom = geom
        station.save()
        saved += 1
    logger.info(f"Saved {saved} traffic-counter stations.")


def save_eco_counter_stations():
    response = requests.get(settings.ECO_COUNTER_STATIONS_URL)
    assert (
        response.status_code == 200
    ), "Fetching stations from {} , status code {}".format(
        settings.ECO_COUNTER_STATIONS_URL, response.status_code
    )
    response_json = response.json()
    features = response_json["features"]
    saved = 0
    for feature in features:
        station = Station()
        name = feature["properties"]["Nimi"]
        if not Station.objects.filter(name=name).exists():
            station.name = name
            station.csv_data_source = ECO_COUNTER
            lon = feature["geometry"]["coordinates"][0]
            lat = feature["geometry"]["coordinates"][1]
            point = Point(lon, lat, srid=4326)
            point.transform(settings.DEFAULT_SRID)
            station.geom = point
            station.save()
            saved += 1
    logger.info(
        "Retrieved {numloc} eco-counter stations, saved {saved} stations.".format(
            numloc=len(features), saved=saved
        )
    )


def gen_eco_counter_test_csv(keys, start_time, end_time):
    """
    Generates testdata for a given timespan,
    for every 15min the value 1 is set.
    """
    df = pd.DataFrame(columns=keys)
    df.keys = keys
    cur_time = start_time
    c = 0
    while cur_time <= end_time:
        # Add value to all keys(sensor stations)
        vals = [1 for x in range(len(keys) - 1)]
        vals.insert(0, str(cur_time))
        df.loc[c] = vals
        cur_time = cur_time + timedelta(minutes=15)
        c += 1
    return df
