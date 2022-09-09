import io
import json
import logging
from datetime import date, timedelta

import dateutil.parser
import pandas as pd
import requests
from django.conf import settings
from django.contrib.gis.gdal import DataSource as DataSource
from django.contrib.gis.geos import GEOSGeometry, Point

from eco_counter.models import (
    ECO_COUNTER,
    LAM_COUNTER,
    Station,
    TRAFFIC_COUNTER,
    TRAFFIC_COUNTER_END_YEAR,
    TRAFFIC_COUNTER_START_YEAR,
)
from eco_counter.tests.test_import_counter_data import (
    ECO_COUNTER_TEST_COLUMNS,
    TRAFFIC_COUNTER_TEST_COLUMNS,
)
from mobility_data.importers.utils import get_root_dir

logger = logging.getLogger("eco_counter")

TRAFFIC_COUNTER_METADATA_GEOJSON = "traffic_counter_metadata.geojson"
# LAM stations located in the municipalities list are included.
LAM_STATION_MUNICIPALITIES = ["Turku", "Raisio", "Kaarina", "Lieto"]
# LAM_STATION_MUNICIPALITIES = ["Turku"]
LAM_STATIONS_API_FETCH_URL = (
    settings.LAM_COUNTER_API_BASE_URL
    + "?api=liikennemaara&tyyppi=h&pvm={start_date}&loppu={end_date}"
    + "&lam_type=option1&piste={id}&luokka=kaikki&suunta={direction}&sisallytakaistat=0"
)

TIMESTAMP_COL_NAME = "startTime"


LAM_STATIONS_DIRECTION_MAPPINGS = {
    "1_Piikkiö": "P",
    "1_Naantali": "P",
    "2_Naantali": "K",
    "1_Turku": "K",
    "2_Turku": "K",
    "2_Helsinki": "P",
    "1_Suikkila": "K",
    "2_Artukainen": "P",
    "1_Vaasa": "P",
    "1_Kuusisto": "P",
    "2_Kaarina": "K",
    "1_Tampere": "P",
    "1_Hämeenlinna": "P",
}
# Create a dict where the years to be importer are keys and the value is the url of the csv data.
# e.g. {2015, "https://data.turku.fi/2yxpk2imqi2mzxpa6e6knq/2015_laskenta.csv"}
keys = [k for k in range(TRAFFIC_COUNTER_START_YEAR, TRAFFIC_COUNTER_END_YEAR + 1)]
TRAFFIC_COUNTER_CSV_URLS = dict(
    [
        (k, f"{settings.TRAFFIC_COUNTER_OBSERVATIONS_BASE_URL}{k}_laskenta.csv")
        for k in keys
    ]
)


class LAMStation:
    def __init__(self, feature):
        self.lam_id = feature["tmsNumber"].as_int()
        names = json.loads(feature["names"].as_string())
        self.name = names["fi"]
        self.name_sv = names["sv"]
        self.name_en = names["en"]
        # The source data has a obsolete Z dimension with value 0, remove it.
        geom = feature.geom.clone()
        geom.coord_dim = 2
        self.geom = GEOSGeometry(geom.wkt, srid=4326)
        self.geom.transform(settings.DEFAULT_SRID)


def get_traffic_counter_metadata_data_layer():
    meta_file = f"{get_root_dir()}/eco_counter/data/{TRAFFIC_COUNTER_METADATA_GEOJSON}"
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


def get_traffic_counter_csv(start_year=2015):
    df = get_dataframe(TRAFFIC_COUNTER_CSV_URLS[start_year])
    # Concat the Traffic counter CSV data into one CSV.
    for key in TRAFFIC_COUNTER_CSV_URLS.keys():
        # Skip start year as it is in the initial dataframe, skip also
        # data from years before the start year.
        if key <= start_year:
            continue
        concat_df = get_dataframe(TRAFFIC_COUNTER_CSV_URLS[key])
        # ignore_index=True, do not use the index values along the concatenation axis.
        # The resulting axis will be labeled 0, …, n - 1.
        df = pd.concat([df, concat_df], ignore_index=True)

    data_layer = get_traffic_counter_metadata_data_layer()

    ids_not_found = 0
    # Rename columns using the metadata to format: name_type|direction
    # e.g. Yliopistonkatu AK
    for feature in data_layer:
        id = feature["Mittauspisteiden_ID"].as_int()
        direction = feature["Suunta"].as_string()
        # TODO, remove when the final/corrected version of the metadata is available
        direction = "K"
        measurement_type = feature["Tyyppi"].as_string()
        # with the id find the column from the data csv
        name = feature["Osoite_fi"].as_string()
        regex = rf".*\({id}\)"
        column = df.filter(regex=regex)
        if len(column.keys()) > 1:
            logger.error(f"Multiple ids: {id}, found in csv data, skipping.")
            continue
        if len(column.keys()) == 0:
            logger.warning(f"ID:{id} in metadata not found in csv data")
            ids_not_found += 1
            continue
        col_name = column.keys()[0]
        new_name = f"{name} {measurement_type}{direction}"
        # Rename the column with the new name that is built from the metadata.
        df.columns = df.columns.str.replace(col_name, new_name, regex=False)
        df[new_name] = df[new_name].fillna(0).astype("int")

    # drop columns with number, i.e. not in metadata as the new column
    # names are in format name_type|direction and does not contain numbers
    df = df.drop(df.filter(regex="[0-9]+").columns, axis=1)
    # Combine columns with same name, i.e. combines lanes into one.
    # axis=1, split along columns.
    df = df.groupby(df.columns, axis=1).sum()
    logger.info(df.info(verbose=False))
    # Move column 'startTime to first (0) position.
    df.insert(0, TIMESTAMP_COL_NAME, df.pop(TIMESTAMP_COL_NAME))
    # df.to_csv("tc_out.csv")
    return df


def get_lam_dataframe(csv_url):
    response = requests.get(csv_url)
    string_data = response.content
    csv_data = pd.read_csv(io.StringIO(string_data.decode("utf-8")), delimiter=";")
    return csv_data


def get_lam_station_dataframe(id, direction, start_date, end_date):
    url = LAM_STATIONS_API_FETCH_URL.format(
        id=id, direction=direction, start_date=start_date, end_date=end_date
    )
    df = get_lam_dataframe(url)
    return df


def get_lam_counter_csv(start_date):
    """
    This function returns the lam counter data in a format supported by the counter.
    startDate, station_name |Type|direction
    e.g.:
    startTime,Tie 8 Raisio AP,Tie 8 Raisio AK,
    0,2010-01-01 00:00:00,168,105
    1,2010-01-01 00:00:15,138,45

    1. Creates a dataframe and generate a column(startTime) with timestamps for every 15min
    2. For every station fetch the csv data with the given start_date to the current day.
    3. The source data is in format
    257;yt1851_Turku_Härkämäki;20141024;2;Artukainen;*;Kaikki;kaikki;30;7;13;14;34;137;478;768;551;523;528;585;647;634;700;762;745;890;698;515;282;171;90;77;9879
    Drop the non data column.
    Transpose every row and as there are data only for every hour, add threee consecutive 0 values
    after every hour value.
    4. Add a column for every stations both directions with the transposed and filled data.
    5. Shift the columns with the calculated shift_index, this must be done if there is no data
    for the station from the start_date. This ensures the data matches the timestamps.

    """

    today = date.today().strftime("%Y-%m-%d")
    start_time = dateutil.parser.parse(f"{start_date}-T00:00")
    end_time = dateutil.parser.parse(f"{today}-T23:45")
    dif_time = end_time - start_time
    # TODO, add 1 ?
    num_15min_freq = dif_time.total_seconds() / 60 / 15
    # TODO capsulate to own function
    # TODO Daylight saving , leap year
    # tz= 'Europe/Helsinki'
    time_stamps = pd.date_range(start_time, freq="15T", periods=num_15min_freq)

    data_frame = pd.DataFrame()
    data_frame[TIMESTAMP_COL_NAME] = time_stamps
    for station in Station.objects.filter(csv_data_source=LAM_COUNTER):
        # In source data the directions are 1 and 2.
        for direction in range(1, 3):
            df = get_lam_station_dataframe(station.lam_id, direction, start_date, today)
            # Read the direction
            direction_name = df["suuntaselite"].iloc[0]
            # From the mappings determine the keskustaan päin or poispäin keskustasta direction.
            direction_value = LAM_STATIONS_DIRECTION_MAPPINGS[
                f"{direction}_{direction_name}"
            ]
            start_time = dateutil.parser.parse(f"{str(df['pvm'].iloc[0])}-T00:00")
            # Calculate shift index, i.e., if data starts from different position that the start_date.
            # then shift the rows to the correct position using the calculated shift_index.
            shift_index = data_frame.index[
                getattr(data_frame, TIMESTAMP_COL_NAME) == str(start_time)
            ][0]
            column_name = f"{station.name} A{direction_value}"
            # Drop non data columns from the beginning of the dataframe
            df.drop(df.iloc[:, 0:8], inplace=True, axis=1)
            # Drop last "Yhteensä" columns
            df = df.iloc[:, :-1]
            values = []
            for _, row in df.iterrows():
                i = 0
                # Transpose and add 3 consecutive 0 values
                for e in range(len(row) * 4):
                    if e % 4 == 0:
                        values.append(row[i])
                        i += 1
                    else:
                        values.append(0)

            data_frame[column_name] = pd.Series(values)
            data_frame[column_name] = data_frame[column_name].fillna(0).astype("int")
            data_frame[column_name] = data_frame[column_name].shift(
                periods=shift_index, axis=0, fill_value=0
            )
    # data_frame.to_csv("lam_out.csv")
    return data_frame


def save_lam_counter_stations():
    data_layer = DataSource(settings.LAM_COUNTER_STATIONS_URL)[0]
    saved = 0
    for feature in data_layer:
        if feature["municipality"].as_string() in LAM_STATION_MUNICIPALITIES:
            station_obj = LAMStation(feature)
            if Station.objects.filter(name=station_obj.name).exists():
                continue
            station = Station()
            station.lam_id = station_obj.lam_id
            station.name = station_obj.name
            station.name_sv = station_obj.name_sv
            station.name_en = station_obj.name_en
            station.csv_data_source = LAM_COUNTER
            station.geom = station_obj.geom
            station.save()
            saved += 1
    logger.info(f"Saved {saved} Lam Counter stations.")


def save_traffic_counter_stations():
    """
    Saves the stations defined in the metadata to Station table.
    """
    saved = 0
    data_layer = get_traffic_counter_metadata_data_layer()
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
    logger.info(f"Saved {saved} Traffic Counter stations.")


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

    logger.info(f"Saved {saved} Eco Counter stations.")


def get_traffic_counter_test_dataframe():
    """
    Generate a Dataframe with only column names for testing. The dataframe
    will then be populated with generated values. The reason for this is
    to avoid calling the very slow get_traffic_counter_csv function to only
    get the column names which is needed for generating testing data.
    """
    return pd.DataFrame(columns=TRAFFIC_COUNTER_TEST_COLUMNS)


def get_eco_counter_test_dataframe():
    return pd.DataFrame(columns=ECO_COUNTER_TEST_COLUMNS)


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
