import io
import logging
from datetime import date, timedelta

import dateutil.parser
import pandas as pd
import requests
from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry, LineString, MultiLineString, Point

from eco_counter.constants import (
    COUNTERS,
    ECO_COUNTER,
    INDEX_COLUMN_NAME,
    LAM_COUNTER,
    LAM_STATION_LOCATIONS,
    LAM_STATION_USER_HEADER,
    LAM_STATIONS_API_FETCH_URL,
    LAM_STATIONS_DIRECTION_MAPPINGS,
    TELRAAM_COUNTER,
    TELRAAM_COUNTER_API_TIME_FORMAT,
    TELRAAM_COUNTER_CAMERA_SEGMENTS_URL,
    TELRAAM_COUNTER_CAMERAS,
    TELRAAM_COUNTER_CAMERAS_URL,
    TELRAAM_COUNTER_CSV_FILE,
    TELRAAM_CSV,
    TELRAAM_HTTP,
    TELRAAM_STATIONS_INITIAL_WKT_GEOMETRIES,
    TRAFFIC_COUNTER,
    TRAFFIC_COUNTER_CSV_URLS,
    TRAFFIC_COUNTER_METADATA_GEOJSON,
)
from eco_counter.models import ImportState, Station
from eco_counter.tests.test_import_counter_data import TEST_COLUMN_NAMES
from mobility_data.importers.utils import get_root_dir

logger = logging.getLogger("eco_counter")


class LAMStation:
    def __init__(self, feature):
        self.station_id = feature["tmsNumber"].as_int()
        self.name = self.name_sv = self.name_en = feature["name"].as_string()
        # The source data has a obsolete Z dimension with value 0, remove it.
        geom = feature.geom.clone()
        geom.coord_dim = 2
        self.location = GEOSGeometry(geom.wkt, srid=4326)
        self.location.transform(settings.DEFAULT_SRID)


class EcoCounterStation:
    def __init__(self, feature):
        self.name = feature["properties"]["Nimi"]
        lon = feature["geometry"]["coordinates"][0]
        lat = feature["geometry"]["coordinates"][1]
        self.location = Point(lon, lat, srid=4326)
        self.location.transform(settings.DEFAULT_SRID)


class TrafficCounterStation:
    def __init__(self, feature):
        self.name = feature["Osoite_fi"].as_string()
        self.name_sv = feature["Osoite_sv"].as_string()
        self.name_en = feature["Osoite_en"].as_string()
        geom = GEOSGeometry(feature.geom.wkt, srid=feature.geom.srid)
        geom.transform(settings.DEFAULT_SRID)
        self.location = geom


# class TelraamCounterStation:
#     # The Telraam API return the coordinates in EPSGS 31370
#     SOURCE_SRID = 4326
#     TARGET_SRID = settings.DEFAULT_SRID

#     def __init__(self, feature):
#         self.name = feature["mac"]
#         self.name_sv = feature["mac"]
#         self.name_en = feature["mac"]
#         self.location, self.geometry = get_telraam_camera_location_and_geometry(
#             feature["segment_id"], self.SOURCE_SRID, self.TARGET_SRID
#         )
#         self.station_id = feature["mac"]


class ObservationStation(LAMStation, EcoCounterStation, TrafficCounterStation):
    def __init__(self, csv_data_source, feature):
        self.csv_data_source = csv_data_source
        self.name = None
        self.name_sv = None
        self.name_en = None
        self.location = None
        self.geometry = None
        self.station_id = None
        match csv_data_source:
            # case COUNTERS.TELRAAM_COUNTER:
            #     TelraamCounterStation.__init__(self, feature)
            case COUNTERS.LAM_COUNTER:
                LAMStation.__init__(self, feature)
            case COUNTERS.ECO_COUNTER:
                EcoCounterStation.__init__(self, feature)
            case COUNTERS.TRAFFIC_COUNTER:
                TrafficCounterStation.__init__(self, feature)


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
    df.insert(0, INDEX_COLUMN_NAME, df.pop(INDEX_COLUMN_NAME))
    # df.to_csv("tc_out.csv")
    return df


def get_lam_dataframe(csv_url):
    response = requests.get(csv_url, headers=LAM_STATION_USER_HEADER)
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
    data_frame[INDEX_COLUMN_NAME] = time_stamps
    for station in Station.objects.filter(csv_data_source=LAM_COUNTER):
        # In the source data the directions are 1 and 2.
        for direction in range(1, 3):
            df = get_lam_station_dataframe(
                station.station_id, direction, start_date, today
            )
            # Read the direction, e.g., Vaasa
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
                getattr(data_frame, INDEX_COLUMN_NAME) == str(start_time)
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


def has_list_elements_in_string(elements, string):
    for element in elements:
        if element in string:
            return True
    return False


def get_lam_counter_stations():
    stations = []
    data_layer = DataSource(settings.LAM_COUNTER_STATIONS_URL)[0]
    for feature in data_layer:
        if has_list_elements_in_string(
            LAM_STATION_LOCATIONS, feature["name"].as_string()
        ):
            stations.append(ObservationStation(LAM_COUNTER, feature))
    return stations


def get_traffic_counter_stations():
    stations = []
    data_layer = get_traffic_counter_metadata_data_layer()
    for feature in data_layer:
        stations.append(ObservationStation(TRAFFIC_COUNTER, feature))
    return stations


def get_eco_counter_stations():
    stations = []
    response = requests.get(settings.ECO_COUNTER_STATIONS_URL)
    assert (
        response.status_code == 200
    ), "Fetching stations from {} , status code {}".format(
        settings.ECO_COUNTER_STATIONS_URL, response.status_code
    )
    response_json = response.json()
    features = response_json["features"]
    for feature in features:
        stations.append(ObservationStation(ECO_COUNTER, feature))
    return stations


def fetch_telraam_camera(mac_id):
    headers = {
        "X-Api-Key": settings.TELRAAM_TOKEN,
    }
    url = TELRAAM_COUNTER_CAMERAS_URL.format(mac_id=mac_id)
    response = TELRAAM_HTTP.get(url, headers=headers)
    cameras = response.json().get("camera", None)
    if cameras:
        # Return first camera, as currently only one camera is
        # returned in Turku by mac_id
        return cameras[0]
    else:
        return None


def get_telraam_cameras():
    cameras = []
    for camera in TELRAAM_COUNTER_CAMERAS.items():
        fetched_camera = fetch_telraam_camera(camera[0])
        if fetched_camera:
            cameras.append(fetched_camera)
        else:
            logger.warning(f"Could not fetch camera {camera[0]}")
    return cameras


def get_telraam_counter_stations():
    stations = []
    cameras = get_telraam_cameras()
    for feature in cameras:
        stations.append(ObservationStation(TELRAAM_COUNTER, feature))
    return stations


def get_telraam_camera_location_and_geometry(id, source_srid=4326, target_srid=3067):
    url = TELRAAM_COUNTER_CAMERA_SEGMENTS_URL.format(id=id)
    headers = {
        "X-Api-Key": settings.TELRAAM_TOKEN,
    }
    response = TELRAAM_HTTP.get(url, headers=headers)
    assert (
        response.status_code == 200
    ), "Could not fetch segment for camera {id}".format(id=id)
    json_data = response.json()
    if len(json_data["features"]) == 0:
        logger.error(f"No data for Telraam camera with segment_id: {id}")
        return None, None

    coords = json_data["features"][0]["geometry"]["coordinates"]
    lss = []
    for coord in coords:
        ls = LineString(coord, srid=source_srid)
        lss.append(ls)
    geometry = MultiLineString(lss, srid=source_srid)
    geometry.transform(target_srid)
    mid_line = round(len(coords) / 2)
    mid_point = round(len(coords[mid_line]) / 2)
    location = Point(coords[mid_line][mid_point], srid=source_srid)
    location.transform(target_srid)
    return location, geometry


def get_telraam_dataframe(mac, day, month, year):
    csv_file = TELRAAM_COUNTER_CSV_FILE.format(
        mac=mac,
        day=day,
        month=month,
        year=year,
    )
    comment_lines = []
    skiprows = 0
    with open(csv_file, "r") as file:
        for line in file:
            if line.startswith("#"):
                comment_lines.append(line)
                skiprows += 1
            else:
                break
    return (
        pd.read_csv(csv_file, index_col=False, skiprows=skiprows),
        csv_file,
        comment_lines,
    )


class TelraamStation:
    def __init__(self, mac, location, geometry):
        self.mac = mac
        self.location = location
        self.geometry = geometry


def parse_telraam_comment_lines(comment_lines):
    location = None
    geometry = None
    comment_lines = [c.replace("# ", "") for c in comment_lines]
    if len(comment_lines) > 0:
        location = GEOSGeometry(comment_lines[0])
    if len(comment_lines) > 1:
        geometry = GEOSGeometry(comment_lines[1])
    return location, geometry


def get_telraam_data_frames(from_date):
    try:
        import_state = ImportState.objects.get(csv_data_source=TELRAAM_CSV)
    except ImportState.DoesNotExist:
        logger.error("ImportState instance not found.")
        return None
    end_date = date(
        import_state.current_year_number,
        import_state.current_month_number,
        import_state.current_day_number,
    )
    data_frames = {}
    for c_i, camera in enumerate(get_telraam_cameras()):
        df_cam = pd.DataFrame()
        start_date = from_date
        current_station = None
        prev_comment_lines = []

        while start_date <= end_date:
            try:
                df_tmp, csv_file, comment_lines = get_telraam_dataframe(
                    camera["mac"], start_date.day, start_date.month, start_date.year
                )
            except FileNotFoundError:
                logger.warning(
                    f"File {csv_file} not found, skipping day{str(start_date)} for camera {camera}"
                )
            else:
                df_cam = pd.concat([df_cam, df_tmp])
            finally:
                if not comment_lines and not current_station:
                    # Set the initial station, e.i, no coordinates defined in CSV source data
                    current_station = TelraamStation(
                        mac=camera["mac"],
                        location=GEOSGeometry(
                            TELRAAM_STATIONS_INITIAL_WKT_GEOMETRIES[camera["mac"]][
                                "location"
                            ]
                        ),
                        geometry=GEOSGeometry(
                            TELRAAM_STATIONS_INITIAL_WKT_GEOMETRIES[camera["mac"]][
                                "geometry"
                            ]
                        ),
                    )
                    data_frames[current_station] = []
                elif comment_lines and not current_station:
                    location, geometry = parse_telraam_comment_lines(comment_lines)
                    current_station = TelraamStation(
                        mac=camera["mac"], location=location, geometry=geometry
                    )

                if prev_comment_lines != comment_lines:
                    location, geometry = parse_telraam_comment_lines(comment_lines)
                    # CSV files might contain the initial coordinates, to avoid creating duplicated check coordinates
                    if (
                        location.wkt != current_station.location.wkt
                        and geometry.wkt != current_station.geometry.wkt
                    ):
                        df_cam[INDEX_COLUMN_NAME] = pd.to_datetime(
                            df_cam[INDEX_COLUMN_NAME],
                            format=TELRAAM_COUNTER_API_TIME_FORMAT,
                        )
                        data_frames[current_station].append(df_cam)
                        current_station = TelraamStation(
                            mac=camera["mac"], location=location, geometry=geometry
                        )
                        data_frames[current_station] = []

                prev_comment_lines = comment_lines
                start_date += timedelta(days=1)

        df_cam[INDEX_COLUMN_NAME] = pd.to_datetime(
            df_cam[INDEX_COLUMN_NAME], format=TELRAAM_COUNTER_API_TIME_FORMAT
        )
        data_frames[current_station].append(df_cam)

    return data_frames


def get_or_create_telraam_station(station):
    name = str(station.mac)
    obj, _ = Station.objects.get_or_create(
        csv_data_source=TELRAAM_COUNTER,
        name=name,
        name_sv=name,
        name_en=name,
        location=station.location,
        geometry=station.geometry,
        station_id=station.mac,
    )
    return obj


def save_stations(csv_data_source):
    stations = []
    num_created = 0
    match csv_data_source:
        # case COUNTERS.TELRAAM_COUNTER:
        # Telraam station are handled differently as they are dynamic
        case COUNTERS.LAM_COUNTER:
            stations = get_lam_counter_stations()
        case COUNTERS.ECO_COUNTER:
            stations = get_eco_counter_stations()
        case COUNTERS.TRAFFIC_COUNTER:
            stations = get_traffic_counter_stations()
    object_ids = list(
        Station.objects.filter(csv_data_source=csv_data_source).values_list(
            "id", flat=True
        )
    )
    for station in stations:
        obj, created = Station.objects.get_or_create(
            name=station.name,
            name_sv=station.name_sv,
            name_en=station.name_en,
            location=station.location,
            geometry=station.geometry,
            station_id=station.station_id,
            csv_data_source=csv_data_source,
        )
        if obj.id in object_ids:
            object_ids.remove(obj.id)
        if created:
            num_created += 1
    Station.objects.filter(id__in=object_ids).delete()
    logger.info(
        f"Deleted {len(object_ids)} obsolete Stations for counter {csv_data_source}"
    )
    num_stations = Station.objects.filter(csv_data_source=csv_data_source).count()
    logger.info(
        f"Created {num_created} Stations of total {num_stations} Stations for counter {csv_data_source}."
    )


def get_test_dataframe(counter):
    """
    Generate a Dataframe with only column names for testing. The dataframe
    will then be populated with generated values. The reason for this is
    to avoid calling the very slow get_traffic_counter_csv function to only
    get the column names which is needed for generating testing data.
    """
    return pd.DataFrame(columns=TEST_COLUMN_NAMES[counter])


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
