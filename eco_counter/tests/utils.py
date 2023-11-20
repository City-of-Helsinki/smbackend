from datetime import timedelta

import pandas as pd
from django.contrib.gis.geos import GEOSGeometry

from eco_counter.management.commands.utils import (
    gen_eco_counter_test_csv,
    TelraamStation,
)


def get_telraam_data_frames_test_fixture(
    from_date,
    num_cameras=1,
    num_locations=2,
    num_days_per_location=2,
):
    def get_location_and_geometry(i):
        location = GEOSGeometry(f"POINT({i} {i})")
        geometry = GEOSGeometry(
            f"MULTILINESTRING (({i} {i}, 1 1), (1 1, 2 2), (2 2, 3 3))"
        )
        return location, geometry

    if num_locations <= 0 or num_cameras <= 0 or num_days_per_location <= 0:
        raise ValueError(
            "'num_locations', 'num_cameras' and 'num_days_per_location' must be greated than 0."
        )

    column_types = ["AK", "AP", "PK", "PP"]
    data_frames = {}
    for c_c in range(num_cameras):
        for l_c in range(num_locations):
            index = c_c + l_c + from_date.year + from_date.month * from_date.day
            location, geometry = get_location_and_geometry(index)
            station = TelraamStation(c_c, location, geometry)
            data_frames[station] = []
            columns = [f"{c_c} {t}" for t in column_types]
            df = pd.DataFrame()
            # Generate 'num_days_per_location' days of data for every location
            start_date = from_date
            for day in range(num_days_per_location):
                csv_data = gen_eco_counter_test_csv(
                    columns, start_date, start_date + timedelta(hours=23), freq="1h"
                )
                start_date += timedelta(days=1)
                df = pd.concat([df, csv_data])
            data_frames[station].append(df)
    return data_frames
