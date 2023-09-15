from unittest.mock import patch

import pytest
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    get_root_dir,
    save_to_database,
)
from mobility_data.models import MobileUnit


@pytest.mark.django_db
@patch("mobility_data.importers.disabled_and_no_staff_parking.get_geojson_file_name")
def test_geojson_import(get_geojson_file_name_mock, municipalities):
    from mobility_data.importers.disabled_and_no_staff_parking import (
        DISABLED_PARKING_CONTENT_TYPE_NAME,
        get_no_staff_parking_objects,
        NO_STAFF_PARKING_CONTENT_TYPE_NAME,
    )

    get_geojson_file_name_mock.return_value = (
        f"{get_root_dir()}/mobility_data/tests/data/autopysäköinti_eihlö.geojson"
    )
    no_stuff_parking_objects, disabled_parking_objects = get_no_staff_parking_objects()
    content_type = get_or_create_content_type_from_config(
        NO_STAFF_PARKING_CONTENT_TYPE_NAME
    )
    num_created, num_deleted = save_to_database(no_stuff_parking_objects, content_type)
    assert num_created == 2
    assert num_deleted == 0
    content_type = get_or_create_content_type_from_config(
        DISABLED_PARKING_CONTENT_TYPE_NAME
    )
    num_created, num_deleted = save_to_database(disabled_parking_objects, content_type)
    assert num_created == 1
    assert num_deleted == 0
    assert MobileUnit.objects.all().count() == 3
    try:
        turku_muni = Municipality.objects.get(name="Turku")
    except Municipality.DoesNotExist:
        assert turku_muni

    kupittaan_maauimala = MobileUnit.objects.get(name="Kupittaan maauimala")
    assert kupittaan_maauimala.content_types.all().count() == 1
    assert (
        kupittaan_maauimala.content_types.first().type_name
        == DISABLED_PARKING_CONTENT_TYPE_NAME
    )
    assert kupittaan_maauimala
    assert kupittaan_maauimala.name_sv == "Kuppis utebad"
    assert kupittaan_maauimala.name_en == "Kupittaa outdoor pool"
    assert kupittaan_maauimala.address_fi == "Blomberginaukio 12"
    assert kupittaan_maauimala.address_sv == "Blombergsplan 12"
    assert kupittaan_maauimala.address_en == "Blomberginaukio 12"
    assert kupittaan_maauimala.extra["invapaikkoja"] == 1
    assert kupittaan_maauimala.address_zip == "20520"
    assert kupittaan_maauimala.municipality == turku_muni
    assert kupittaan_maauimala.extra["rajoitustyyppi"]["fi"] == "Erityisalue"
    assert kupittaan_maauimala.extra["rajoitustyyppi"]["sv"] == "Specialområde"
    assert kupittaan_maauimala.extra["rajoitustyyppi"]["en"] == "Special area"
    kupittaan_seikkailupuisto = MobileUnit.objects.get(name="Kupittaan seikkailupuisto")
    assert (
        kupittaan_seikkailupuisto.content_types.first().type_name
        == NO_STAFF_PARKING_CONTENT_TYPE_NAME
    )
    assert kupittaan_seikkailupuisto
    assert kupittaan_seikkailupuisto.address_sv == "Tahkogränden 5"
    assert kupittaan_seikkailupuisto.extra["paikkoja_y"] == 9
    assert kupittaan_seikkailupuisto.extra["rajoitustyyppi"]["fi"] == "Erityisalue"
    assert kupittaan_seikkailupuisto.extra["rajoitustyyppi"]["sv"] == "Specialområde"
    assert kupittaan_seikkailupuisto.extra["rajoitustyyppi"]["en"] == "Special area"

    kupittaan_urheiluhalli = MobileUnit.objects.get(name="Kupittaan urheiluhalli")
    assert kupittaan_urheiluhalli
    assert (
        kupittaan_urheiluhalli.content_types.first().type_name
        == NO_STAFF_PARKING_CONTENT_TYPE_NAME
    )
    assert kupittaan_urheiluhalli.name_en == "Kupittaa sports hall"
    assert kupittaan_urheiluhalli.extra["sahkolatauspaikkoja"] == 42
    assert kupittaan_urheiluhalli.extra["tolppapaikkoja"] == 24
    assert kupittaan_urheiluhalli.extra["aikarajoitus"] == "7-15"
    assert kupittaan_urheiluhalli.extra["lastauspiste"]["fi"] == "Kyllä"
    assert kupittaan_urheiluhalli.extra["lastauspiste"]["sv"] == "Ja"
    assert kupittaan_urheiluhalli.extra["lastauspiste"]["en"] == "Yes"
    assert kupittaan_urheiluhalli.extra["paivays"] == "2021/06/03"
    assert kupittaan_urheiluhalli.extra["lisatietoja"]["fi"] == "Käynti Maariankadulta"
    assert kupittaan_urheiluhalli.extra["lisatietoja"]["sv"] == "Ingång från Mariegatan"
    assert (
        kupittaan_urheiluhalli.extra["lisatietoja"]["en"] == "Entrance from Maariankatu"
    )
    assert kupittaan_urheiluhalli.extra["lisatietoja"]["fi"] == "Käynti Maariankadulta"
    assert kupittaan_urheiluhalli.extra["rajoitustyyppi"]["fi"] == "Kiekkopysäköinti"
    assert (
        kupittaan_urheiluhalli.extra["rajoitustyyppi"]["sv"]
        == "Parkering med parkeringsskiva"
    )
    assert kupittaan_urheiluhalli.extra["rajoitustyyppi"]["en"] == "Disc parking"
    assert kupittaan_urheiluhalli.extra["maksuvyohyke"] == 2
    assert kupittaan_urheiluhalli.extra["max_aika_h"] == 3.0
    assert kupittaan_urheiluhalli.extra["max_aika_m"] == 180.0
    assert kupittaan_urheiluhalli.extra["rajoitus_maksul_arki"] == "1-2"
    assert kupittaan_urheiluhalli.extra["rajoitus_maksul_l"] == "2-3"
    assert kupittaan_urheiluhalli.extra["rajoitus_maksul_s"] == "3-4"
    assert kupittaan_urheiluhalli.extra["rajoitettu_ark"] == "7-21"
    assert kupittaan_urheiluhalli.extra["rajoitettu_l"] == "2-4"
    assert kupittaan_urheiluhalli.extra["rajoitettu_s"] == "4-6"
    assert kupittaan_urheiluhalli.extra["rajoit_lisat"]["fi"] == "Invapaikka"
    assert kupittaan_urheiluhalli.extra["rajoit_lisat"]["sv"] == "Invalidfordon"
    assert (
        kupittaan_urheiluhalli.extra["rajoit_lisat"]["en"]
        == "Vehicles for disabled persons"
    )
