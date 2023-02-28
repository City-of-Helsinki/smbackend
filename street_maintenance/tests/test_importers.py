from unittest.mock import patch

import pytest

from street_maintenance.management.commands.constants import INFRAROAD
from street_maintenance.models import MaintenanceUnit, MaintenanceWork

from .utils import (
    get_infraroad_units_mock_data,
    get_infraroad_works_mock_data,
    get_kuntec_units_mock_data,
    get_kuntec_works_mock_data,
    get_yit_contract_mock_data,
    get_yit_event_types_mock_data,
    get_yit_routes_mock_data,
    get_yit_vehicles_mock_data,
)


@pytest.mark.django_db
@patch("street_maintenance.management.commands.utils.get_yit_vehicles")
def test_yit_units(
    get_yit_vehicles_mock,
    administrative_division,
    administrative_division_geometry,
):
    from street_maintenance.management.commands.utils import (
        create_yit_maintenance_units,
    )

    get_yit_vehicles_mock.return_value = get_yit_vehicles_mock_data(2)
    num_created_units, num_del_units = create_yit_maintenance_units("test_access_token")
    assert MaintenanceUnit.objects.count() == 2
    assert num_created_units == 2
    assert num_del_units == 0
    unit = MaintenanceUnit.objects.first()
    unit_id = unit.id
    assert unit.names == ["Huoltoauto"]
    assert unit.unit_id == "82260ff7-589e-4cee-a8e0-124b615381f1"
    get_yit_vehicles_mock.return_value = get_yit_vehicles_mock_data(1)
    num_created_units, num_del_units = create_yit_maintenance_units("test_access_token")
    assert unit.id == unit_id
    assert num_created_units == 0
    assert num_del_units == 1
    assert MaintenanceUnit.objects.count() == 1


@pytest.mark.django_db
@patch(
    "street_maintenance.management.commands.utils.get_yit_vehicles",
    return_value=get_yit_vehicles_mock_data(2),
)
@patch(
    "street_maintenance.management.commands.utils.get_yit_contract",
    return_value=get_yit_contract_mock_data(),
)
@patch(
    "street_maintenance.management.commands.utils.get_yit_event_types",
    return_value=get_yit_event_types_mock_data(),
)
@patch("street_maintenance.management.commands.utils.get_yit_routes")
def test_yit_works(
    get_yit_routes_mock,
    get_yit_vechiles_mock,
    administrative_division,
    administrative_division_geometry,
):
    from street_maintenance.management.commands.utils import (
        create_yit_maintenance_units,
        create_yit_maintenance_works,
    )

    create_yit_maintenance_units("test_access_token")
    get_yit_routes_mock.return_value = get_yit_routes_mock_data(2)
    num_created_works, num_del_works = create_yit_maintenance_works(
        "test_access_token", 3
    )
    assert num_created_works == 2
    assert num_del_works == 0
    assert MaintenanceWork.objects.count() == 2
    work = MaintenanceWork.objects.first()
    work_id = work.id
    assert work.events == ["liukkaudentorjunta"]
    assert work.original_event_names == ["Suolaus"]
    get_yit_routes_mock.return_value = get_yit_routes_mock_data(1)
    num_created_works, num_del_works = create_yit_maintenance_works(
        "test_access_token", 3
    )
    assert num_created_works == 0
    assert num_del_works == 1
    assert work.id == work_id
    assert MaintenanceWork.objects.count() == 1


@pytest.mark.django_db
@patch("street_maintenance.management.commands.utils.get_json_data")
def test_kuntec(
    get_json_data_mock, administrative_division, administrative_division_geometry
):
    from street_maintenance.management.commands.utils import (
        create_kuntec_maintenance_units,
        create_kuntec_maintenance_works,
    )

    # Note, the fixture JSON contains one unit item with IO_DIN state 0(off)
    # i.e., will not be included
    get_json_data_mock.return_value = get_kuntec_units_mock_data(2)
    num_created_units, num_del_units = create_kuntec_maintenance_units()
    assert num_created_units == 2
    assert num_del_units == 0
    assert MaintenanceUnit.objects.count() == 2
    unit = MaintenanceUnit.objects.first()
    unit_id = unit.id
    assert unit.unit_id == "150635"
    assert unit.names == ["Auraus"]
    get_json_data_mock.return_value = get_kuntec_units_mock_data(1)
    num_created_units, num_del_units = create_kuntec_maintenance_units()
    assert unit.id == unit_id
    assert num_created_units == 0
    assert num_del_units == 1
    assert MaintenanceUnit.objects.count() == 1
    get_json_data_mock.return_value = get_kuntec_works_mock_data(2)
    num_created_works, num_del_works = create_kuntec_maintenance_works(3)
    assert num_created_works == 2
    assert num_del_works == 0
    assert MaintenanceWork.objects.count() == 2
    work = MaintenanceWork.objects.first()
    work_id = work.id
    work.events = ["auraus"]
    work.original_event_names = ["Auraus"]
    get_json_data_mock.return_value = get_kuntec_works_mock_data(1)
    num_created_works, num_del_works = create_kuntec_maintenance_works(3)
    assert num_created_works == 0
    assert num_del_works == 1
    assert work.id == work_id
    assert MaintenanceWork.objects.count() == 1


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
    get_json_data_mock.return_value = get_infraroad_units_mock_data(2)
    num_created_units, num_del_units = create_maintenance_units(INFRAROAD)
    assert MaintenanceUnit.objects.count() == 2
    assert num_created_units == 2
    assert num_del_units == 0
    unit = MaintenanceUnit.objects.first()
    unit_id = unit.id
    unit.unit_id = "2817625"
    unit.names = ["au"]
    get_json_data_mock.return_value = get_infraroad_units_mock_data(1)
    num_created_units, num_del_units = create_maintenance_units(INFRAROAD)
    assert unit.id == unit_id
    assert num_created_units == 0
    assert num_del_units == 1
    assert MaintenanceUnit.objects.count() == 1
    get_json_data_mock.return_value = get_infraroad_works_mock_data(3)
    num_created_works, num_del_works = create_maintenance_works(INFRAROAD, 1, 10)
    assert num_created_works == 3
    assert num_del_works == 0
    assert MaintenanceWork.objects.count() == 3
    work = MaintenanceWork.objects.first()
    work_id = work.id
    work.events = ["auraus"]
    work.original_event_names = ["au"]
    get_json_data_mock.return_value = get_infraroad_works_mock_data(1)
    num_created_works, num_del_works = create_maintenance_works(INFRAROAD, 1, 10)
    assert num_created_works == 0
    assert num_del_works == 2
    assert work.id == work_id
    assert MaintenanceWork.objects.count() == 1
