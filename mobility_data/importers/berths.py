import csv
import os

from django.contrib.gis.geos import Point

from services.utils import strtobool

from .utils import FieldTypes, get_file_name_from_data_source, get_root_dir

# Default name of the file, if not added to DataSource.
BERTH_CVS_FILE = "Venepaikkojen_tiedot.csv"

# Column used to match the marina and berth in csv file.
NAME_COLUMN = "PaakohdeNimi"

X_COORDINATE_COLUMN = "KeskipisteI"
Y_COORDINATE_COLUMN = "KeskipisteP"

SOURCE_DATA_SRID = 3877
TRANSFROM_TO_SRID = 4326

column_mappings = {
    "Varaustyyppi": {"type": FieldTypes.STRING},
    "Kohdetyyppi": {"type": FieldTypes.STRING},
    "VarauksenTila": {"type": FieldTypes.STRING},
    "TuoreimmanVarauksenPaatymisaikaUtc": {"type": FieldTypes.STRING},
    "Varaustapa": {"type": FieldTypes.STRING},
    "Varattavissa": {"type": FieldTypes.STRING},
    "HintaAlv0": {"type": FieldTypes.FLOAT},
    "HintaAlv%": {"type": FieldTypes.FLOAT},
    "Aktiivinen": {"type": FieldTypes.BOOLEAN},
    X_COORDINATE_COLUMN: {"type": FieldTypes.FLOAT},
    Y_COORDINATE_COLUMN: {"type": FieldTypes.FLOAT},
}

# NOTE, berths are an exception, as they do not have a real content type relation.
# They are assigned to the marina data as extra data.
CONTENT_TYPE_NAME = "Berth"


def get_berths(berth_name):
    berths = []
    column_indexes = {}
    file_path = get_file_name_from_data_source(CONTENT_TYPE_NAME)
    if not file_path:
        data_path = os.path.join(get_root_dir(), "mobility_data/data")
        file_path = os.path.join(data_path, BERTH_CVS_FILE)
    with open(file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")

        for i, row in enumerate(csv_reader):
            if i == 0:
                # Determine the indexes for columns by their names.
                for column in column_mappings:
                    column_indexes[column] = row.index(column)
                name_col_index = row.index(NAME_COLUMN)

            if row[name_col_index] == berth_name:
                berth = {}
                for column in column_mappings:
                    match column_mappings[column]["type"]:
                        case FieldTypes.STRING:
                            berth[column] = row[column_indexes[column]]
                        case FieldTypes.FLOAT:
                            berth[column] = float(row[column_indexes[column]])
                        case FieldTypes.BOOLEAN:
                            berth[column] = bool(strtobool(row[column_indexes[column]]))
                    # As Leaflet requires coordinates in srid 4326 we provide such.
                    geometry = Point(
                        float(row[column_indexes[X_COORDINATE_COLUMN]]),
                        float(row[column_indexes[Y_COORDINATE_COLUMN]]),
                        srid=SOURCE_DATA_SRID,
                    )
                    geometry.transform(TRANSFROM_TO_SRID)
                    berth[f"{X_COORDINATE_COLUMN}_4326"] = geometry.x
                    berth[f"{Y_COORDINATE_COLUMN}_4326"] = geometry.y
                berths.append(berth)
    return berths
