import io
import json
import logging
from datetime import date, timedelta

import dateutil.parser
import pandas as pd
import requests
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, Point

from eco_counter.constants import (
    ECO_COUNTER,
    LAM_COUNTER,
    LAM_STATION_MUNICIPALITIES,
    LAM_STATIONS_API_FETCH_URL,
    LAM_STATIONS_DIRECTION_MAPPINGS,
    TIMESTAMP_COL_NAME,
    TRAFFIC_COUNTER,
    TRAFFIC_COUNTER_CSV_URLS,
    TRAFFIC_COUNTER_METADATA_GEOJSON,
)
from eco_counter.models import Station
from eco_counter.tests.test_import_counter_data import TEST_COLUMN_NAMES
from mobility_data.importers.utils import get_root_dir

logger = logging.getLogger("eco_counter")


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
    """
    This function returns traffic counter data in a format supported by the counter.
    1. For every year there is a separate csv file. Fetch them and concate into one.
    2. With the metadata set the column names to station_name|Type|direction format
    e.g.:
    startTime,Aninkaistenkatu/Eerikinkatu AK,Aninkaistenkatu/Eerikinkatu BK
    0,2015-01-01T00:00,105,79
    0,2015-01-01T00:15,125,89
    3. Merge columns with same name into one column, i.e., merges lanes into one column.
    """
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
    # df.to_csv("tc_concat.csv")
    data_layer = get_traffic_counter_metadata_data_layer()
    ids_not_found = 0
    # Rename columns using the metadata to format: name_type|direction
    # e.g. Yliopistonkatu AK
    for feature in data_layer:
        id = feature["Mittauspisteiden_ID"].as_int()
        direction = feature["Suunta"].as_string()
        measurement_type = feature["Tyyppi"].as_string()
        # Use the id to find the column from the CSV data
        name = feature["Osoite_fi"].as_string()
        regex = rf".*\({id}\)$"
        column = df.filter(regex=regex)
        if len(column.keys()) > 1:
            # TODO, for some reason the concat makes a duplicate row ID???
            logger.error(f"Multiple ids: {id}, found in CSV data, skipping.")
            continue
        if len(column.keys()) == 0:
            logger.warning(f"ID: {id} in metadata not found in CSV data.")
            ids_not_found += 1
            continue
        col_name = column.keys()[0]
        new_name = f"{name} {measurement_type}{direction}"
        # Rename the column with the new name that is built from the metadata.
        df.columns = df.columns.str.replace(col_name, new_name, regex=False)
        df[new_name] = df[new_name].fillna(0).astype("int")

    # drop columns with number, i.e. not in metadata as the new column
    # names are in format name_type|direction and does not contain numbers
    df = df.drop(df.filter(regex=r"\([0-9]+\)$").columns, axis=1)

    # Combine columns with same name, i.e. combines lanes into one.
    # axis=1, split along columns.
    df = df.groupby(by=df.columns, axis=1).sum()

    logger.info(df.info(verbose=False))
    logger.info(f"{ids_not_found} IDs not found in metadata.")
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
    This function returns the LAM counter data in a format supported by the counter.
    startDate, station_name|Type|direction
    e.g.:
    startTime,Tie 8 Raisio AP,Tie 8 Raisio AK,
    0,2010-01-01 00:00:00,168,105
    1,2010-01-01 00:00:15,138,45

    1. Creates a dataframe and generate a column(startTime) with timestamps for every 15min
    2. For every station fetch the csv data with the given start_date to the current day.
    3. The source data is in format
    257;yt1851_Turku_Härkämäki;20141024;2;Artukainen;*;Kaikki;kaikki;30;7;13;14;34;137;478;768;551;523;528;585;647;634;700;762;745;890;698;515;282;171;90;77;9879
    Drop the non data column.
    Transpose every row and as there are data only for every hour, add three consecutive zero values
    after every hour value.
    4. Add a column for every station and both directions with the transposed and filled data.
    5. Shift the columns with the calculated shift_index, this must be done if there is no data
    for the station from the start_date. This ensures the data matches the timestamps.
    """

    drop_columns = [
        "pistetunnus",
        "sijainti",
        "suunta",
        "suuntaselite",
        "kaista",
        "jaottelu",
        "ajoneuvoluokka",
        "yhteensa",
    ]
    source_data_timestamp_format = "%Y%m%d"
    today = date.today().strftime("%Y-%m-%d")
    start_time = dateutil.parser.parse(f"{start_date}-T00:00")
    end_time = dateutil.parser.parse(f"{today}-T23:45")
    dif_time = end_time - start_time
    num_15min_freq = dif_time.total_seconds() / 60 / 15
    time_stamps = pd.date_range(start_time, freq="15T", periods=num_15min_freq)
    data_frame = pd.DataFrame()
    data_frame[TIMESTAMP_COL_NAME] = time_stamps
    for station in Station.objects.filter(csv_data_source=LAM_COUNTER):
        # In the source data the directions are 1 and 2.
        for direction in range(1, 3):
            df = get_lam_station_dataframe(station.lam_id, direction, start_date, today)
            # Read the direction
            direction_name = df["suuntaselite"].iloc[0]
            # From the mappings determine the 'keskustaan päin' or 'poispäin keskustasta' direction.
            try:
                direction_value = LAM_STATIONS_DIRECTION_MAPPINGS[
                    f"{direction}_{direction_name}"
                ]
            except KeyError as e:
                logger.warning(f"Discarding station {station} KeyError: {e}")
                continue
            start_time = dateutil.parser.parse(f"{str(df['pvm'].iloc[0])}-T00:00")
            # Calculate shift index, i.e., if data starts from different position that the start_date.
            # then shift the rows to the correct position using the calculated shift_index.
            shift_index = data_frame.index[
                getattr(data_frame, TIMESTAMP_COL_NAME) == str(start_time)
            ][0]
            column_name = f"{station.name} A{direction_value}"
            # Drop all unnecessary columns.
            df.drop(columns=drop_columns, inplace=True, axis=1)
            values = []
            current_date = start_time
            for _, row in df.iterrows():
                # The source data can miss data, this must be handled and filled with zero values.
                current_time_str = current_date.strftime(source_data_timestamp_format)
                row_timestamp_str = str(int(row[0]))
                if current_time_str != row_timestamp_str:
                    # Loop until a day with data is found and add zero values for the days not found in data.
                    while True:
                        logger.warning(
                            f"{station.name} has no data for {current_date.strftime(source_data_timestamp_format)} "
                        )
                        # Add zero values for a day.
                        values.extend([0] * 24 * 4)
                        if row_timestamp_str == str(
                            current_date.strftime(source_data_timestamp_format)
                        ):
                            break
                        else:
                            current_date += timedelta(days=1)
                else:
                    # Start with index 1, as the first column contains the timestamp
                    i = 1
                    # Transpose(i.e., add values to a list which is then assigned to a column)
                    # and add 3 consecutive 0 values.
                    for e in range(1, (len(row) - 1) * 4 + 1):
                        if e % 4 == 0:
                            values.append(row[i])
                            i += 1
                        else:
                            values.append(0)
                current_date += timedelta(days=1)

            data_frame[column_name] = pd.Series(values)
            data_frame[column_name] = data_frame[column_name].fillna(0).astype("int")
            if shift_index > 0:
                data_frame[column_name] = data_frame[column_name].shift(
                    periods=shift_index, axis=0, fill_value=0
                )
    return data_frame


def save_lam_counter_stations():
    data_layer = DataSource(settings.LAM_COUNTER_STATIONS_URL)[0]
    saved = 0
    for feature in data_layer:
        if feature["municipality"].as_string() in LAM_STATION_MUNICIPALITIES:
            station_obj = LAMStation(feature)
            station, _ = Station.objects.get_or_create(
                name=station_obj.name,
                csv_data_source=LAM_COUNTER,
                lam_id=station_obj.lam_id,
                geom=station_obj.geom,
            )
            station.name_sv = station_obj.name_sv
            station.name_en = station_obj.name_en
            station.save()
            saved += 1
    logger.info(f"Saved {saved} LAM Counter stations.")


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


def get_test_dataframe(counter):
    """
    Generate a Dataframe with only column names for testing. The dataframe
    will then be populated with generated values. The reason for this is
    to avoid calling the very slow get_traffic_counter_csv function to only
    get the column names which is needed for generating testing data.
    """
    return pd.DataFrame(columns=TEST_COLUMN_NAMES[counter])


# def gen_eco_counter_test_csv(keys, start_time, end_time):
#     """
#     Generates test data for a given timespan,
#     for every row (15min) the value 1 is set.
#     """
#     df = pd.DataFrame(columns=keys)
#     df.keys = keys
#     cur_time = start_time
#     c = 0
#     while cur_time <= end_time:
#         # Add value to all keys(sensor stations)
#         vals = [1 for x in range(len(keys) - 1)]
#         vals.insert(0, str(cur_time))
#         df.loc[c] = vals
#         cur_time = cur_time + timedelta(minutes=15)
#         c += 1
#     return df


def gen_eco_counter_test_csv(
    columns, start_time, end_time, time_stamp_column="startTime"
):
    """
    Generates test data for a given timespan,
    for every row (15min) the value 1 is set.
    """
    df = pd.DataFrame()
    timestamps = pd.date_range(start=start_time, end=end_time, freq="15min")
    for col in columns:
        vals = [1 for i in range(len(timestamps))]
        df.insert(0, col, vals)
    df.insert(0, time_stamp_column, timestamps)
    return df
