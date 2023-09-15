import json
import os
from io import StringIO

from django.contrib.gis.gdal import DataSource
from django.core.management import call_command


def import_command(command, *args, **kwargs):
    """
    call_command used when running importer in tests. Parameter command
    is the used import command e.g. "import_payment_zones".
    """
    out = StringIO()
    call_command(
        command,
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )


def get_test_fixture_json_data(file_name):
    data_path = os.path.join(os.path.dirname(__file__), "data")
    file = os.path.join(data_path, file_name)
    with open(file) as f:
        data = json.load(f)
    return data


def get_data_source(file_name):
    """
    Returns the given file_name as a GDAL Datasource,
    the file must be located in /mobility_data/tests/data/
    """
    data_path = os.path.join(os.path.dirname(__file__), "data")
    file = os.path.join(data_path, file_name)
    return DataSource(file)


def get_test_fixture_data_layer(file_name):
    ds = get_data_source(file_name)
    assert len(ds) == 1
    return ds[0]


def get_test_fixture_data_source(file_name):
    return get_data_source(file_name)
