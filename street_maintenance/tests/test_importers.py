from datetime import datetime
from unittest.mock import patch

import pytest

from street_maintenance.management.commands.constants import DATE_FORMATS, INFRAROAD
from street_maintenance.models import MaintenanceUnit, MaintenanceWork


def get_infraroad_works_json_data(num_elements):
    current_date = datetime.now().date().strftime(DATE_FORMATS[INFRAROAD])
    location_history = [
        {
            "timestamp": f"{current_date} 08:29:49",
            "coords": "(22.24957474 60.49515401)",
            "events": ["au"],
        },
        {
            "timestamp": f"{current_date} 08:29:28",
            "coords": "(22.24946401 60.49515848)",
            "events": ["au"],
        },
        {
            "timestamp": f"{current_date} 08:28:32",
            "coords": "(22.24944127 60.49519463)",
            "events": ["hiekoitus"],
        },
    ]
    assert num_elements <= len(location_history)
    data = {"location_history": location_history[:num_elements]}
    return data


def get_infraroad_units_json_data(num_elements):
    current_date = datetime.now().date().strftime(DATE_FORMATS[INFRAROAD])
    data = [
        {
            "id": 2817625,
            "last_location": {
                "timestamp": f"{current_date} 06:31:34",
                "coords": "(22.249642023816705 60.49569119699299)",
                "events": ["au"],
            },
        },
        {
            "id": 12891825,
            "last_location": {
                "timestamp": f"{current_date} 08:29:49",
                "coords": "(22.24957474 60.49515401)",
                "events": ["Kenttien hoito"],
            },
        },
    ]
    assert num_elements <= len(data)
    return data[:num_elements]


@pytest.mark.django_db
@patch("street_maintenance.management.commands.utils.get_json_data")
def test_infraroad(
    get_json_data_mock, administrative_division, administrative_division_geometry
):
    from street_maintenance.management.commands.utils import (
        create_maintenance_units,
        create_maintenance_works,
    )

    # Test unit creation
    get_json_data_mock.return_value = get_infraroad_units_json_data(2)
    num_created_units, num_del_units = create_maintenance_units(INFRAROAD)
    assert MaintenanceUnit.objects.count() == 2
    assert num_created_units == 2
    assert num_del_units == 0
    unit = MaintenanceUnit.objects.first()
    unit.unit_id = "2817625"
    unit.names = ["au"]
    get_json_data_mock.return_value = get_infraroad_units_json_data(1)
    num_created_units, num_del_units = create_maintenance_units(INFRAROAD)
    assert unit.id == MaintenanceUnit.objects.first().id
    assert num_created_units == 0
    assert num_del_units == 1
    assert MaintenanceUnit.objects.count() == 1
    get_json_data_mock.return_value = get_infraroad_works_json_data(3)
    num_created_works, num_del_works = create_maintenance_works(INFRAROAD, 1, 10)
    assert num_created_works == 3
    assert num_del_works == 0
    assert MaintenanceWork.objects.count() == 3
    work = MaintenanceWork.objects.first()
    work.events = ["auraus"]
    work.original_event_names = ["au"]
    get_json_data_mock.return_value = get_infraroad_works_json_data(1)
    num_created_works, num_del_works = create_maintenance_works(INFRAROAD, 1, 10)
    assert num_created_works == 0
    assert num_del_works == 2
    assert work.id == MaintenanceWork.objects.first().id
    assert MaintenanceWork.objects.count() == 1
