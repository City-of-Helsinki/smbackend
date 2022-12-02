import uuid

import pytest
from django.contrib.gis.geos import Point
from django.utils.timezone import now
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionType,
    Municipality,
    Street,
)
from rest_framework.test import APIClient

from services.management.commands.index_search_columns import get_search_column
from services.management.commands.services_import.services import (
    update_service_counts,
    update_service_node_counts,
    update_service_root_service_nodes,
)
from services.models import (
    Department,
    Service,
    ServiceNode,
    Unit,
    UnitAccessibilityShortcomings,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def units(
    services,
    service_nodes,
    municipality,
    department,
    administrative_division,
    administrative_division_type,
):
    unit = Unit.objects.create(
        id=1,
        name="Terveysasema",
        last_modified_time=now(),
        www="www.test.com",
        phone="02020242",
        municipality=municipality,
    )
    unit.services.add(1)
    unit.save()
    unit = Unit.objects.create(
        id=2,
        name="Biologinen museo",
        name_sv="Biologiska museet",
        name_en="Biological Museum",
        street_address_fi="Neitsytpolku 1",
        municipality=municipality,
        displayed_service_owner_type="municipal_service",
        displayed_service_owner_fi="kunnallinen palvelu",
        displayed_service_owner_sv="kommunal tjänst",
        displayed_service_owner_en="municipal service",
        department=department,
        last_modified_time=now(),
        location=Point(22.24, 60.44, srid=4326),
    )
    # Add service Museot
    unit.services.add(2)
    # Add service_node Museot
    unit.service_nodes.add(2)
    unit.save()
    # id=3 is the "Uimahalli" service
    service = Service.objects.get(id=3)
    unit = Unit.objects.create(
        id=3,
        name="Impivaara",
        service_names_fi=[service.name_fi],
        last_modified_time=now(),
        municipality=municipality,
    )
    unit.services.add(3)
    unit.save()
    update_service_root_service_nodes()
    update_service_counts()
    update_service_node_counts()
    Unit.objects.update(search_column_fi=get_search_column(Unit, "fi"))
    return Unit.objects.all()


@pytest.mark.django_db
@pytest.fixture
def department(municipality):
    return Department.objects.create(
        uuid=uuid.uuid4(),
        name="Test Department",
        street_address="Test Address 42",
        municipality=municipality,
    )


@pytest.mark.django_db
@pytest.fixture
def accessibility_shortcoming(units):
    return UnitAccessibilityShortcomings.objects.create(
        unit=units[1], accessibility_shortcoming_count={"rollator": 5, "stroller": 1}
    )


@pytest.mark.django_db
@pytest.fixture
def services():
    Service.objects.create(
        id=1,
        name="test service",
        last_modified_time=now(),
    )
    Service.objects.create(
        id=2,
        name="Museot",
        name_sv="Museum",
        name_en="Museum",
        last_modified_time=now(),
    )
    Service.objects.create(
        id=3,
        name="Uimahalli",
        name_sv="Simhall",
        last_modified_time=now(),
    )
    Service.objects.update(search_column_fi=get_search_column(Service, "fi"))
    return Service.objects.all()


@pytest.mark.django_db
@pytest.fixture
def service_nodes(services):
    leisure = ServiceNode.objects.create(
        id=1,
        name="Vapaa-aika",
        name_sv="Fritid",
        name_en="Leisure",
        last_modified_time=now(),
    )
    museums = ServiceNode.objects.create(
        id=2,
        parent=leisure,
        name="Museot",
        name_sv="Museer",
        name_en="Museums",
        last_modified_time=now(),
    )
    museums.related_services.add(2)
    museums.save()
    ServiceNode.objects.update(search_column_fi=get_search_column(ServiceNode, "fi"))
    return ServiceNode.objects.all()


@pytest.mark.django_db
@pytest.fixture
def addresses(streets, municipality):
    Address.objects.create(
        municipality_id=municipality.id,
        location=Point(60.479032, 22.25417, srid=4326),
        id=1,
        street_id=42,
        number=1,
        number_end=2,
        letter="A",
        full_name="Kurrapolku 1A",
        full_name_sv="Kurrastigen 1A",
        full_name_en="Kurrapolku 1A",
    )
    Address.objects.create(
        municipality_id=municipality.id,
        location=Point(60.379032, 22.15417),
        id=2,
        street_id=43,
        number=1,
        letter="B",
        full_name="Markulantie 2B",
    )
    Address.objects.create(
        municipality_id=municipality.id,
        location=Point(60.45484552050515, 22.273209685057232),
        id=3,
        street_id=44,
        number=5,
        full_name="Yliopistonkatu 5",
    )
    Address.objects.create(
        municipality_id=municipality.id,
        location=Point(60.45264337230143, 22.264875756221265),
        id=4,
        street_id=44,
        number=21,
        full_name="Yliopistonkatu 21",
    )
    Address.objects.create(
        municipality_id=municipality.id,
        location=Point(60.45015934221425, 22.258536898549355),
        id=5,
        street_id=44,
        number=33,
        full_name="Yliopistonkatu 33",
    )
    Address.objects.update(search_column_fi=get_search_column(Address, "fi"))
    return Address.objects.all()


@pytest.mark.django_db
@pytest.fixture
def municipality():
    return Municipality.objects.create(
        division_id=1, id="helsinki", name="Helsinki", name_sv="Helsingfors"
    )


@pytest.mark.django_db
@pytest.fixture
def administrative_division_type():
    return AdministrativeDivisionType.objects.get_or_create(
        id=1, type="muni", name="Municipality"
    )


@pytest.mark.django_db
@pytest.fixture
def administrative_division(administrative_division_type):
    adm_div = AdministrativeDivision.objects.get_or_create(
        id=1, name="Helsinki", origin_id=853, type_id=1
    )
    AdministrativeDivision.objects.update(
        search_column_fi=get_search_column(AdministrativeDivision, "fi")
    )
    return adm_div


@pytest.mark.django_db
@pytest.fixture
def streets():
    Street.objects.create(
        id=42, name="Kurrapolku", name_sv="Kurrastigen", municipality_id="helsinki"
    )
    Street.objects.create(id=43, name="Markulantie", municipality_id="helsinki")
    Street.objects.create(id=44, name="Yliopistonkatu", municipality_id="helsinki")
    return Street.objects.all()
