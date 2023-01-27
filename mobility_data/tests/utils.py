import json
import os
from io import StringIO

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
