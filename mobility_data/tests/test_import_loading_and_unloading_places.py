from unittest.mock import patch

import pytest
from munigeo.models import Municipality

from mobility_data.importers.utils import (
    get_or_create_content_type_from_config,
    get_root_dir,
    save_to_database,
)
from mobility_data.models import ContentType, MobileUnit


@pytest.mark.django_db
@patch("mobility_data.importers.loading_unloading_places.get_geojson_file_name")
def test_import(get_geojson_file_name_mock, municipalities):
    from mobility_data.importers.loading_unloading_places import (
        CONTENT_TYPE_NAME,
        get_loading_and_unloading_objects,
    )

    file_name = f"{get_root_dir()}/mobility_data/tests/data/loading_and_unloading_places.geojson"
    get_geojson_file_name_mock.return_value = file_name
    content_type = get_or_create_content_type_from_config(CONTENT_TYPE_NAME)
    objects = get_loading_and_unloading_objects()
    num_created, num_deleted = save_to_database(objects, content_type)
    assert num_created == 3
    assert num_deleted == 0
    assert ContentType.objects.all().count() == 1
    assert MobileUnit.objects.all().count() == 3
    turku_muni = None
    try:
        turku_muni = Municipality.objects.get(name="Turku")
    except Municipality.DoesNotExist:
        assert turku_muni
    lantinen_rantakatu = MobileUnit.objects.get(name="Läntinen Rantakatu")
    assert lantinen_rantakatu.content_types.all().count() == 1
    assert lantinen_rantakatu.content_types.first().type_name == CONTENT_TYPE_NAME
    assert lantinen_rantakatu.name_sv == "Östra Strandgatan"
    assert lantinen_rantakatu.name_en == "Läntinen Rantakatu"
    assert lantinen_rantakatu.address_fi == "Läntinen Rantakatu 13"
    assert lantinen_rantakatu.address_sv == "Östra Strandgatan 13"
    assert lantinen_rantakatu.address_en == "Läntinen Rantakatu 13"
    assert lantinen_rantakatu.address_zip == "20700"
    assert lantinen_rantakatu.municipality == turku_muni

    assert lantinen_rantakatu.extra["lastauspiste"]["fi"] == "Lastausalue"
    assert lantinen_rantakatu.extra["lastauspiste"]["sv"] == "Lastningsplats"
    assert lantinen_rantakatu.extra["lastauspiste"]["en"] == "Loading zone"

    assert lantinen_rantakatu.extra["Saavutettavuus"]["fi"] == "Kadunvarsipysäköinti"
    assert lantinen_rantakatu.extra["Saavutettavuus"]["sv"] == "Parkering på gata"
    assert lantinen_rantakatu.extra["Saavutettavuus"]["en"] == "On-street parking"

    assert lantinen_rantakatu.extra["rajoitustyyppi"]["fi"] == "Erityisalue"
    assert lantinen_rantakatu.extra["rajoitustyyppi"]["sv"] == "Specialområde"
    assert lantinen_rantakatu.extra["rajoitustyyppi"]["en"] == "Special area"

    assert lantinen_rantakatu.extra["paikkoja_y"] == 2
