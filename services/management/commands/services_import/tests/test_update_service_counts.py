import pytest
from django.utils.timezone import now
from munigeo.models import (
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
)
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from services.management.commands.services_import.services import update_service_counts
from services.models import Service, ServiceUnitCount, Unit, UnitServiceDetails


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def municipality_type():
    o = AdministrativeDivisionType.objects.create(type="muni")
    o.save()
    return o


@pytest.fixture
def municipalities(municipality_type):
    os = []
    for muni_name in ["Helsinki", "Vantaa"]:
        o = AdministrativeDivision.objects.create(
            type=municipality_type, name=muni_name
        )
        o.save()
        m = Municipality.objects.create(
            name=muni_name, id=muni_name.lower(), division=o
        )
        m.save()
        os.append(m)
    return os


@pytest.fixture
def services():
    os = []
    for i in range(0, 5):
        o = Service.objects.create(
            name="service{}".format(i), id=i, last_modified_time=now()
        )
        o.save()
        os.append(o)
    return os


@pytest.fixture
def units(services, municipalities):
    units = []
    max_unit_count = 5
    index = 1
    unit_id = 0
    distinct_service_muni_counts = set()
    unit_names = set()
    for municipality in municipalities:
        for service in services:
            if index % max_unit_count > 0:
                distinct_service_muni_counts.add((service.id, municipality.id))
            for i in range(0, index % max_unit_count):
                name = "unit_s{}_m{}_{}".format(service.id, municipality.id, i)
                unit = Unit.objects.create(
                    id=unit_id,
                    municipality=municipality,
                    last_modified_time=now(),
                    name=name,
                )
                unit_names.add(name)
                unit.save()
                usd = UnitServiceDetails.objects.create(unit=unit, service=service)
                usd.save()
                units.append(unit)
                unit_id += 1
            index += 1
    unit_name = "unit_s0_special_case_no_muni"
    unit = Unit.objects.create(
        id=500000, municipality=None, last_modified_time=now(), name=unit_name
    )
    unit_names.add(unit_name)
    usd = UnitServiceDetails.objects.create(unit=unit, service=services[0])
    usd.save()
    units.append(unit)
    # Currently generates the following units
    assert unit_names == set(
        [
            "unit_s0_mhelsinki_0",
            "unit_s0_mvantaa_0",
            "unit_s1_mhelsinki_0",
            "unit_s1_mhelsinki_1",
            "unit_s1_mvantaa_0",
            "unit_s1_mvantaa_1",
            "unit_s2_mhelsinki_0",
            "unit_s2_mhelsinki_1",
            "unit_s2_mhelsinki_2",
            "unit_s2_mvantaa_0",
            "unit_s2_mvantaa_1",
            "unit_s2_mvantaa_2",
            "unit_s3_mhelsinki_0",
            "unit_s3_mhelsinki_1",
            "unit_s3_mhelsinki_2",
            "unit_s3_mhelsinki_3",
            "unit_s3_mvantaa_0",
            "unit_s3_mvantaa_1",
            "unit_s3_mvantaa_2",
            "unit_s3_mvantaa_3",
            "unit_s0_special_case_no_muni",
        ]
    )
    return {"units": units, "count_rows": len(distinct_service_muni_counts) + 1}


@pytest.mark.django_db
def test_update_service_counts(municipalities, services, units, api_client):
    assert ServiceUnitCount.objects.count() == 0

    # Step 1: build count objects
    update_service_counts()
    assert ServiceUnitCount.objects.count() == units["count_rows"]

    response = api_client.get(reverse("service-list", format="json"))
    response_by_id = dict((s["id"], s) for s in response.data["results"])

    assert response_by_id[0]["unit_count"]["municipality"][None] == 1

    assert response_by_id[0]["unit_count"]["municipality"]["helsinki"] == 1
    assert response_by_id[0]["unit_count"]["municipality"]["vantaa"] == 1

    assert response_by_id[1]["unit_count"]["municipality"]["helsinki"] == 2
    assert response_by_id[1]["unit_count"]["municipality"]["vantaa"] == 2

    assert response_by_id[2]["unit_count"]["municipality"]["helsinki"] == 3
    assert response_by_id[2]["unit_count"]["municipality"]["vantaa"] == 3

    assert response_by_id[3]["unit_count"]["municipality"]["helsinki"] == 4
    assert response_by_id[3]["unit_count"]["municipality"]["vantaa"] == 4

    # Step 2: incrementally delete count objects:

    # Step 2 (a) : delete via municipality
    Unit.objects.filter(municipality__name="Vantaa").delete()
    update_service_counts()
    real_count = 1 + (units["count_rows"] - 1) / 2
    assert ServiceUnitCount.objects.count() == real_count

    response = api_client.get(reverse("service-list", format="json"))
    response_by_id = dict((s["id"], s) for s in response.data["results"])
    assert response_by_id[0]["unit_count"]["municipality"][None] == 1
    assert response_by_id[0]["unit_count"]["municipality"]["helsinki"] == 1
    assert response_by_id[1]["unit_count"]["municipality"]["helsinki"] == 2
    assert response_by_id[2]["unit_count"]["municipality"]["helsinki"] == 3
    assert response_by_id[3]["unit_count"]["municipality"]["helsinki"] == 4

    assert "vantaa" not in response_by_id[0]["unit_count"]["municipality"]
    assert "vantaa" not in response_by_id[1]["unit_count"]["municipality"]
    assert "vantaa" not in response_by_id[2]["unit_count"]["municipality"]
    assert "vantaa" not in response_by_id[3]["unit_count"]["municipality"]

    # Step 2 (b) : delete via service
    Unit.objects.filter(services=services[0]).delete()
    real_count -= 1
    update_service_counts()
    assert ServiceUnitCount.objects.count() == real_count

    response = api_client.get(reverse("service-list", format="json"))
    response_by_id = dict((s["id"], s) for s in response.data["results"])
    assert response_by_id[1]["unit_count"]["municipality"]["helsinki"] == 2
    assert response_by_id[2]["unit_count"]["municipality"]["helsinki"] == 3
    assert response_by_id[3]["unit_count"]["municipality"]["helsinki"] == 4

    assert None not in response_by_id[0]["unit_count"]["municipality"]
    assert "helsinki" not in response_by_id[0]["unit_count"]["municipality"]
    assert "vantaa" not in response_by_id[0]["unit_count"]["municipality"]
    assert "vantaa" not in response_by_id[1]["unit_count"]["municipality"]
    assert "vantaa" not in response_by_id[2]["unit_count"]["municipality"]
    assert "vantaa" not in response_by_id[3]["unit_count"]["municipality"]

    # Step 3: delete single unit at a time
    service = Service.objects.get(pk=3)
    units = list(Unit.objects.filter(services=service))

    while len(units) > 0:
        assert service.unit_counts.get(division__name="Helsinki").count == len(units)
        units.pop().delete()
        update_service_counts()
    assert service.unit_counts.count() == 0

    # Step 4: add single unit at a time
    service = Service.objects.get(pk=0)
    count = 0
    for i in range(0, 10):
        u = Unit.objects.create(
            name="test_{}",
            id=i + 100000,
            last_modified_time=now(),
            municipality=municipalities[0],
        )
        u.save()
        UnitServiceDetails.objects.create(unit=u, service=service).save()
        update_service_counts()
        count += 1
        assert count == service.unit_counts.get(division__name="Helsinki").count

    # Step 5: delete everything
    Unit.objects.all().delete()
    update_service_counts()
    assert ServiceUnitCount.objects.count() == 0

    response = api_client.get(reverse("service-list", format="json"))
    for s in response.data["results"]:
        assert len(s["unit_count"]["municipality"]) == 0
