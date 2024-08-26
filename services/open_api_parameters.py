from drf_spectacular.utils import OpenApiParameter

ACCESSIBILITY_DESCRIPTION_PARAMETER = OpenApiParameter(
    name="accessibility_description",
    location=OpenApiParameter.QUERY,
    description="If given displays the accessibility description of unit.",
    required=False,
    type=bool,
)

ANCESTOR_ID_PARAMETER = OpenApiParameter(
    name="ancestor",
    location=OpenApiParameter.QUERY,
    description="Filter by ancestor ID.",
    required=False,
    type=str,
)

BBOX_PARAMETER = OpenApiParameter(
    name="bbox",
    location=OpenApiParameter.QUERY,
    description="Bounding box in the format 'left,bottom,right,top'. Values must be floating points or integers.",
    required=False,
    type=str,
)

BUILDING_NUMBER_PARAMETER = OpenApiParameter(
    name="number",
    location=OpenApiParameter.QUERY,
    description="Filter by building number.",
    required=False,
    type=str,
)

CITY_AS_DEPARTMENT_PARAMETER = OpenApiParameter(
    name="city_as_department",
    location=OpenApiParameter.QUERY,
    description="Filter by city UUID.",
    required=False,
    type=str,
)

DATE_PARAMETER = (
    OpenApiParameter(
        name="date",
        location=OpenApiParameter.QUERY,
        description="Filter divisions based on their validity date. Format: YYYY-MM-DD.",
        required=False,
        type=str,
    ),
)

DISTANCE_PARAMETER = OpenApiParameter(
    name="distance",
    location=OpenApiParameter.QUERY,
    description="The maximum distance from the provided location, defined by the lat and lon parameters. If this"
    " parameter is given also the 'lat' and 'lon' parameters are required.",
    required=False,
    type=float,
)

DIVISION_TYPE_PARAMETER = OpenApiParameter(
    name="type",
    location=OpenApiParameter.QUERY,
    description="Filter by administrative division type or type ID.",
    required=False,
    type=str,
)

GEOMETRY_PARAMETER = OpenApiParameter(
    name="geometry",
    location=OpenApiParameter.QUERY,
    description="Display administrative division boundary.",
    required=False,
    type=bool,
)

ID_PARAMETER = OpenApiParameter(
    name="id",
    location=OpenApiParameter.QUERY,
    description="Filter by ID or list of IDs.",
    required=False,
    type=str,
)

INPUT_PARAMETER = OpenApiParameter(
    name="input",
    location=OpenApiParameter.QUERY,
    description="Filter by partial match of name.",
    required=False,
    type=str,
)

LATITUDE_PARAMETER = OpenApiParameter(
    name="lat",
    location=OpenApiParameter.QUERY,
    description="Filter by location. Give latitude in WGS84 system. If this parameter is given also the 'lon' "
    "parameter is required.",
    required=False,
    type=float,
)

LEVEL_PARAMETER = OpenApiParameter(
    name="level",
    location=OpenApiParameter.QUERY,
    description="Filter by level.",
    required=False,
    type=str,
)

LONGITUDE_PARAMETER = OpenApiParameter(
    name="lon",
    location=OpenApiParameter.QUERY,
    description="Filter by location. Give longitude in WGS84 system. If this parameter is given also the 'lat' "
    "parameter is required.",
    required=False,
    type=float,
)

MUNICIPALITY_PARAMETER = OpenApiParameter(
    name="municipality",
    location=OpenApiParameter.QUERY,
    description="Filter by municipality.",
    required=False,
    type=str,
)

OCD_ID_PARAMETER = OpenApiParameter(
    name="ocd_id",
    location=OpenApiParameter.QUERY,
    description="Filter by OCD ID.",
    required=False,
    type=str,
)

OCD_MUNICIPALITY_PARAMETER = OpenApiParameter(
    name="municipality",
    location=OpenApiParameter.QUERY,
    description="Filter by municipality name or OCD ID.",
    required=False,
    type=str,
)

ORGANIZATION_PARAMETER = OpenApiParameter(
    name="organization",
    location=OpenApiParameter.QUERY,
    description="Filter by organization UUID.",
    required=False,
    type=str,
)

ORIGIN_ID_PARAMETER = OpenApiParameter(
    name="origin_id",
    location=OpenApiParameter.QUERY,
    description="Filter by origin ID.",
    required=False,
    type=str,
)

PROVIDER_TYPE_NOT_PARAMETER = OpenApiParameter(
    name="provider_type__not",
    location=OpenApiParameter.QUERY,
    description="Exclude by provider type numeric value.",
    required=False,
    type=int,
)

PROVIDER_TYPE_PARAMETER = OpenApiParameter(
    name="provider_type",
    location=OpenApiParameter.QUERY,
    description="Filter by provider type numeric value.",
    required=False,
    type=int,
)

STREET_PARAMETER = OpenApiParameter(
    name="street",
    location=OpenApiParameter.QUERY,
    description="Filter by street name.",
    required=False,
    type=str,
)

UNIT_GEOMETRY_3D_PARAMETER = OpenApiParameter(
    name="geometry_3d",
    location=OpenApiParameter.QUERY,
    description="If given displays the 3D geometry of unit if it exists.",
    required=False,
    type=bool,
)

UNIT_GEOMETRY_PARAMETER = OpenApiParameter(
    name="geometry",
    location=OpenApiParameter.QUERY,
    description="If given displays the geometry of unit if it exists.",
    required=False,
    type=bool,
)
