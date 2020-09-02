import json
import os

from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)


def create_municipality():
    division_type, _ = AdministrativeDivisionType.objects.get_or_create(
        id=1, type="muni", defaults={"name": "Municipality"}
    )
    division, _ = AdministrativeDivision.objects.get_or_create(
        type=division_type, id=1, name_fi="Testikunta"
    )

    municipality, _ = Municipality.objects.get_or_create(
        id="Testikunta", name_fi="Testikunta", division=division
    )

    return municipality


def get_ptv_test_resource():
    """
    Mock calling the API by fetching dummy data from file.
    """
    data_path = os.path.join(os.path.dirname(__file__), "test_data")
    file = os.path.join(data_path, "municipality_channels.json")

    with open(file) as f:
        data = json.load(f)
    return data
