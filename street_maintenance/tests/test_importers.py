from unittest.mock import patch

import pytest

from street_maintenance.management.commands.constants import DESTIA, INFRAROAD
from street_maintenance.models import MaintenanceUnit, MaintenanceWork

from .utils import (
    get_fluentprogress_units_mock_data,
    get_fluentprogress_works_mock_data,
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
    assert unit_id == MaintenanceUnit.objects.first().id
    assert num_created_units == 0
    assert num_del_units == 1
    assert MaintenanceUnit.objects.count() == 1
    # Test duplicate unit
    unit_dup = MaintenanceUnit.objects.first()
    unit_dup.pk = 42
    unit_dup.save()
    num_created_units, num_del_units = create_yit_maintenance_units("test_access_token")
    assert num_created_units == 0
    assert num_del_units == 1


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
    assert work_id == MaintenanceWork.objects.first().id
    assert MaintenanceWork.objects.count() == 1
    # Create duplicate work
    work_dup = MaintenanceWork.objects.first()
    work_dup.pk = 42
    work_dup.save()
    num_created_works, num_del_works = create_yit_maintenance_works(
        "test_access_token", 3
    )
    assert num_created_works == 0
    assert num_del_works == 1


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
    assert unit.names == ["Auraus", "Hiekoitus"]
    get_json_data_mock.return_value = get_kuntec_units_mock_data(1)
    num_created_units, num_del_units = create_kuntec_maintenance_units()
    assert unit_id == MaintenanceUnit.objects.first().id
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
    work.events = ["auraus", "liukkaudentorjunta"]
    work.original_event_names = ["Auraus", "Hiekoitus"]
    get_json_data_mock.return_value = get_kuntec_works_mock_data(1)
    num_created_works, num_del_works = create_kuntec_maintenance_works(3)
    assert num_created_works == 0
    assert num_del_works == 1
    assert work_id == MaintenanceWork.objects.first().id
    assert MaintenanceWork.objects.count() == 1
    # Test duplicate unit
    unit_dup = MaintenanceUnit.objects.first()
    unit_dup.pk = 42
    unit_dup.save()
    get_json_data_mock.return_value = get_kuntec_units_mock_data(1)
    num_created_units, num_del_units = create_kuntec_maintenance_units()
    assert num_created_units == 0
    assert num_del_units == 1
    # Create duplicate work
    work_dup = MaintenanceWork.objects.first()
    work_dup.pk = 42
    work_dup.save()
    get_json_data_mock.return_value = get_kuntec_works_mock_data(1)
    num_created_works, num_del_works = create_kuntec_maintenance_works(3)
    assert num_created_works == 0
    assert num_del_works == 1


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
    get_json_data_mock.return_value = get_fluentprogress_units_mock_data(2)
    num_created_units, num_del_units = create_maintenance_units(INFRAROAD)
    assert MaintenanceUnit.objects.count() == 2
    assert num_created_units == 2
    assert num_del_units == 0
    unit = MaintenanceUnit.objects.first()
    unit_id = unit.id
    unit.unit_id = "2817625"
    unit.names = ["au"]
    get_json_data_mock.return_value = get_fluentprogress_units_mock_data(1)
    num_created_units, num_del_units = create_maintenance_units(INFRAROAD)
    assert unit_id == MaintenanceUnit.objects.first().id
    assert num_created_units == 0
    assert num_del_units == 1
    assert MaintenanceUnit.objects.count() == 1
    get_json_data_mock.return_value = get_fluentprogress_works_mock_data(3)
    num_created_works, num_del_works = create_maintenance_works(INFRAROAD, 1, 10)
    assert num_created_works == 3
    assert num_del_works == 0
    assert MaintenanceWork.objects.count() == 3
    work = MaintenanceWork.objects.first()
    work_id = work.id
    work.events = ["auraus"]
    work.original_event_names = ["au"]
    get_json_data_mock.return_value = get_fluentprogress_works_mock_data(1)
    num_created_works, num_del_works = create_maintenance_works(INFRAROAD, 1, 10)
    assert num_created_works == 0
    assert num_del_works == 2
    assert work_id == MaintenanceWork.objects.first().id
    assert MaintenanceWork.objects.count() == 1
    # Test duplicate Unit
    unit_dup = MaintenanceUnit.objects.first()
    unit_dup.pk = 42
    unit_dup.save()
    get_json_data_mock.return_value = get_fluentprogress_units_mock_data(1)
    num_created_units, num_del_units = create_maintenance_units(INFRAROAD)
    assert num_created_units == 0
    assert num_del_units == 1
    # Test duplicate work
    work_dup = MaintenanceWork.objects.first()
    work_dup.pk = 42
    work_dup.save()
    get_json_data_mock.return_value = get_fluentprogress_works_mock_data(1)
    num_created_works, num_del_works = create_maintenance_works(INFRAROAD, 1, 10)
    assert num_created_works == 0
    assert num_del_works == 1


@pytest.mark.django_db
@patch("street_maintenance.management.commands.utils.get_json_data")
def test_destia(
    get_json_data_mock, administrative_division, administrative_division_geometry
):
    from street_maintenance.management.commands.utils import (
        create_maintenance_units,
        create_maintenance_works,
    )

    # Test unit creation
    get_json_data_mock.return_value = get_fluentprogress_units_mock_data(2)
    num_created_units, num_del_units = create_maintenance_units(DESTIA)
    assert MaintenanceUnit.objects.count() == 2
    assert num_created_units == 2
    assert num_del_units == 0
    unit = MaintenanceUnit.objects.first()
    unit_id = unit.id
    unit.unit_id = "2817625"
    unit.names = ["au"]
    get_json_data_mock.return_value = get_fluentprogress_units_mock_data(1)
    num_created_units, num_del_units = create_maintenance_units(DESTIA)
    assert unit_id == MaintenanceUnit.objects.first().id
    assert num_created_units == 0
    assert num_del_units == 1
    assert MaintenanceUnit.objects.count() == 1
    get_json_data_mock.return_value = get_fluentprogress_works_mock_data(3)
    num_created_works, num_del_works = create_maintenance_works(DESTIA, 1, 10)
    assert num_created_works == 3
    assert num_del_works == 0
    assert MaintenanceWork.objects.count() == 3
    work = MaintenanceWork.objects.first()
    work_id = work.id
    work.events = ["auraus"]
    work.original_event_names = ["au"]
    work = MaintenanceWork.objects.get(
        original_event_names=["au", "sivuaura", "sirotin"]
    )
    # Test that duplicate events are not included, as "sivuaura" and "au" are mapped to "auraus"
    assert work.events == ["auraus", "liukkaudentorjunta"]
    get_json_data_mock.return_value = get_fluentprogress_works_mock_data(1)
    num_created_works, num_del_works = create_maintenance_works(DESTIA, 1, 10)
    assert num_created_works == 0
    assert num_del_works == 2
    assert work_id == MaintenanceWork.objects.first().id
    assert MaintenanceWork.objects.count() == 1
