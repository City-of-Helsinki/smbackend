import pytest
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from munigeo.models import (
    Address,
    AdministrativeDivision,
    AdministrativeDivisionGeometry,
    AdministrativeDivisionType,
    Municipality,
    Street,
)
from rest_framework.test import APIClient

from ..models import ContentType, GroupType, MobileUnit, MobileUnitGroup

# borders of Turku in well known text format.
TURKU_WKT = (
    "MULTIPOLYGON (((245370.121 6713650.59, 245058.936 6713448.535, 244279.15 6714124.228, "
    "243438.857 6712982.504, 243910.864 6712448.206, 244460.089 6711826.499, 245266.866 6709451.216, "
    "245077.971 6708906.214, 244865.892 6708294.322, 243260.572 6707443.068, 240930.332 6706207.411, "
    "239767.447 6705590.767, 240148.075 6704083.856, 240373.16 6703192.745, 241197.924 6703081.102, "
    "241384.58 6701972.949, 241481.885 6700941.816, 241681.605 6700245.15, 240956.864 6699162.204, "
    "240008.098 6699378.475, 239241.198 6698998.88, 238235.56 6699101.525, 236900.355 6698434.226, "
    "236347.31 6698852.852, 235792.214 6698209.134, 234899.196 6698220.645, 233449.271 6699015.245, "
    "231163.917 6699468.75, 230061.904 6699111.899, 228597.413 6699757.856, 228193.083 6699615.667, "
    "228253.615 6700171.949, 229188.53 6701412.634, 228322.147 6701702.171, 228011.532 6702274.564, "
    "228764.804 6703783.045, 229590.134 6705435.827, 229470.172 6708168.048, 229072.472 6709282.223, "
    "229751.474 6710366.715, 230780.77 6710476.329, 230992.164 6711298.417, 231097.55 6712047.676, "
    "231867.009 6712835.119, 232691.064 6713037.804, 233750.593 6712819.282, 235620.049 6712433.718, "
    "236039.935 6713266.532, 236800.025 6714774.117, 237925.618 6715645.233, 237999.991 6715302.327, "
    "239212.053 6716883.621, 239031.602 6717088.129, 238408.189 6717771.664, 237832.263 6719201.024, "
    "238266.697 6719326.242, 239225.506 6718845.252, 239613.159 6718301.412, 240176.902 6718406.035, "
    "241438.801 6720231.044, 241672.262 6721001.141, 242636.725 6724182.534, 244013.124 6726471.69, "
    "246938.099 6729125.065, 247806.495 6730482.339, 247936.87 6731148.504, 248007.167 6731507.688, "
    "250110.717 6742255.941, 251719.145 6736864.75, 251589.987 6732957.986, 251038.068 6731421.609, "
    "249886.998 6727200.66, 248900.227 6726191.105, 248460.65 6725741.379, 246300.199 6721309.72, "
    "246228.54 6719343.719, 246667.202 6718822.446, 244825.727 6715370.219, 245832.073 6714528.813, "
    "245370.121 6713650.59)))"
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
@pytest.fixture
def content_type():
    content_type = ContentType.objects.create(
        type_name="TTT", name="test", description="test content type"
    )
    return content_type


@pytest.mark.django_db
@pytest.fixture
def group_type():
    group_type = GroupType.objects.create(
        type_name="TGT", name="test group", description="test group type"
    )
    return group_type


@pytest.mark.django_db
@pytest.fixture
def mobile_unit(content_type):
    mobile_unit = MobileUnit.objects.create(
        name="Test mobileunit",
        description="Test description",
        content_type=content_type,
        geometry=Point(42.42, 21.21, srid=settings.DEFAULT_SRID),
        extra={"test": "4242"},
    )
    return mobile_unit


@pytest.mark.django_db
@pytest.fixture
def mobile_unit_group(group_type):
    mobile_unit_group = MobileUnitGroup.objects.create(
        name="Test mobileunitgroup",
        description="Test description",
        group_type=group_type,
    )
    return mobile_unit_group


@pytest.mark.django_db
@pytest.fixture
def municipality():
    muni = Municipality.objects.create(id="turku", name="Turku")
    return muni


@pytest.mark.django_db
@pytest.fixture
def administrative_division_type():
    adm_div_type = AdministrativeDivisionType.objects.create(
        id=1, type="muni", name="Municipality"
    )
    return adm_div_type


@pytest.mark.django_db
@pytest.fixture
def administrative_division(administrative_division_type):
    adm_div = AdministrativeDivision.objects.get_or_create(
        id=1, name="Turku", origin_id=853, type_id=1
    )
    return adm_div


@pytest.mark.django_db
@pytest.fixture
def administrative_division_geometry(administrative_division):
    turku_multipoly = GEOSGeometry(TURKU_WKT, srid=3067)
    adm_div_geom = AdministrativeDivisionGeometry.objects.create(
        id=1, division_id=1, boundary=turku_multipoly
    )
    return adm_div_geom


@pytest.mark.django_db
@pytest.fixture
def streets():
    streets = []
    street = Street.objects.create(
        name="Test Street",
        name_fi="Test Street",
        name_sv="Test StreetSV",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Linnanpuisto",
        name_fi="Linnanpuisto",
        name_sv="Slottsparken",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Kristiinankatu",
        name_fi="Kristiinankatu",
        name_sv="Kristinegatan",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Pitkäpellonkatu",
        name_fi="Pitkäpellonkatu",
        name_sv="Långåkersgatan",
        municipality_id="turku",
    )
    streets.append(street)
    street = Street.objects.create(
        name="Kupittaankatu",
        name_fi="Kupittaankatu",
        name_sv="Kuppisgatan",
        municipality_id="turku",
    )
    streets.append(street)
    return streets


@pytest.mark.django_db
@pytest.fixture
def address(streets):
    addresses = []
    location = Point(22.244, 60.4, srid=4326)
    address = Address.objects.create(
        id=100,
        location=location,
        street=streets[0],
        number=42,
        full_name_fi="Test Street 42",
        full_name_sv="Test StreetSV 42",
    )
    addresses.append(address)
    location = Point(22.227168, 60.4350612, srid=4326)
    address = Address.objects.create(
        id=101,
        location=location,
        street=streets[1],
        full_name_fi="Linnanpuisto",
        full_name_sv="Slottsparken",
    )
    addresses.append(address)
    location = Point(22.264457, 60.448905, srid=4326)
    address = Address.objects.create(
        id=102,
        location=location,
        street=streets[2],
        number=4,
        full_name_fi="Kristiinankatu 4",
        full_name_sv="Kristinegata 4",
    )
    addresses.append(address)
    location = Point(22.2383, 60.411726, srid=4326)
    address = Address.objects.create(
        id=103,
        location=location,
        street=streets[3],
        number=7,
        full_name_fi="Pitkäpellonkatu 7",
        full_name_sv="Långåkersgatan 7",
    )
    addresses.append(address)
    location = Point(22.2871092678621, 60.44677715747775, srid=4326)
    address = Address.objects.create(
        id=104,
        location=location,
        street=streets[4],
        number=8,
        full_name_fi="Kupittaankatu 8",
        full_name_sv="Kuppisgatan 8",
    )
    addresses.append(address)
    return addresses
