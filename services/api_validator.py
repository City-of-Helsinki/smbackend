import datetime
import re
from typing import List
from uuid import UUID

from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.gdal.error import SRSException
from pydantic import BaseModel, validator

from services.models import Unit, Service, ServiceNode
from smbackend import settings


unit_fields = [u.name for u in Unit._meta.get_fields()]
unit_foreign_fields = [u.name for u in Unit._meta.get_fields() if u.many_to_many or u.one_to_many
                       or u.many_to_one or u.one_to_one]
service_fields = [u.name for u in Service._meta.get_fields()]
service_foreign_fields = [u.name for u in Service._meta.get_fields() if u.many_to_many or u.one_to_many
                          or u.many_to_one or u.one_to_one]
servicenode_fields = [u.name for u in ServiceNode._meta.get_fields()]
servicenode_foreign_fields = [u.name for u in ServiceNode._meta.get_fields() if u.many_to_many or u.one_to_many
                              or u.many_to_one or u.one_to_one]

include_list = ['service_node.' + i for i in servicenode_foreign_fields] +\
               ['service.' + i for i in service_foreign_fields] +\
               ['unit.' + i for i in unit_foreign_fields]
only_list = ['service_node.' + i for i in servicenode_fields] +\
            ['service.' + i for i in service_fields] +\
            ['unit.' + i for i in unit_fields]


class RequestFilters(BaseModel):

    page: int = None
    page_size: int = None
    include: List[str] = None
    service: List[int] = None
    id: List[int] = None
    lat: float = None
    lon: float = None
    distance: float = None
    municipality: List[str] = None
    city_as_department: List[UUID] = None
    provider_type: List[int] = None
    provider_type__not: List[int] = None
    level: str = None
    service_node: List[int] = None
    exclude_service_nodes: List[int] = None
    division: List[str] = None
    bbox: str = None
    bbox_srid: int = None
    geometry: bool = None
    category: List[str] = None
    period: str = None
    maintenance_organization: List[str] = None
    type: List[str] = None

    @validator('municipality', whole=True)
    def check_municipality(cls, v):
        for m in v:
            if not m.startswith('ocd-division') and len(re.findall(r"[\d,.]", m)) > 0:
                raise ValueError("'%s' not a suitable value for municipality'" % m)

    @validator('distance')
    def check_positive(cls, v):
        if not v > 0:
            raise ValueError('distance must be a positive float number')

    @validator('level')
    def check_level(cls, v):
        levels = list(settings.LEVELS.keys())
        levels.append('all')
        if v not in levels:
            raise ValueError('level must be one of: %s' % ', '.join(l for l in levels))

    @validator('category', whole=True)
    def check_category(cls, v):
        for c in v:
            if ':' not in c:
                raise ValueError("'%s' not a valid category" % c)
            else:
                k = c.split(':')[0]
                v = c.split(':')[1]
                try:
                    int(v)
                except ValueError as e:
                    raise ValueError('%s:%s, %s' % (k, v, str(e)))
                if len(re.findall(r"\d", k)) > 0:
                    raise ValueError("value '%s' is not suitable for category" % k)

    @validator('type', whole=True)
    def check_type(cls, v):
        types = ['service_node', 'service', 'unit', 'address']
        if not any(t in types for t in v):
            raise ValueError('type must be one of: %s' % ', '.join(t for t in types))

    @validator('bbox_srid')
    def check_srid(cls, v, values):
        bbox = [float(a) for a in values['bbox'].split(',')]

        tm35_bbox = settings.BOUNDING_BOX
        wgs84_bbox = settings.WGS84_BBOX

        try:
            srs = SpatialReference(v)
        except SRSException as e:
            raise ValueError(str(e))

        cs = srs.attr_value('PROJCS') if srs.attr_value('PROJCS') else srs.attr_value('GEOGCS')
        if cs not in settings.ACCEPTED_SRID:
            raise ValueError('coordinate system must be: %s, was %s'
                             % (', '.join(s for s in settings.ACCEPTED_SRID), cs))

        if cs == 'WGS 84':
            check_wgs84 = wgs84_bbox[0] <= bbox[0] <= wgs84_bbox[2] and wgs84_bbox[1] <= bbox[1] <= wgs84_bbox[3] \
                and wgs84_bbox[0] <= bbox[2] <= wgs84_bbox[2] and wgs84_bbox[1] <= bbox[3] <= wgs84_bbox[3]
            if not check_wgs84:
                raise ValueError('some of bbox values are out of bound: %s.' % bbox)

        else:
            check_tm35 = tm35_bbox[0] <= bbox[0] <= tm35_bbox[2] and tm35_bbox[1] <= bbox[1] <= tm35_bbox[3] \
                and tm35_bbox[0] <= bbox[2] <= tm35_bbox[2] and tm35_bbox[1] <= bbox[3] <= tm35_bbox[3]
            if not check_tm35:
                raise ValueError('some of bbox values are out of bound: %s.' % bbox)

    @validator('period')
    def check_period(cls, v):
        try:
            datetime.datetime.strptime(v, '%Y')
        except ValueError:
            raise ValueError('Period must be year in YYYY format, %s given' % v)


class SearchRequestFilters(BaseModel):

    input: str = None
    q: str = None
    language: List[str] = None
    include: List[str] = None
    only: List[str] = None

    @validator('language')
    def check_languages(cls, v):
        lang_codes = [x[0] for x in settings.LANGUAGES]
        if v not in lang_codes:
            raise ValueError("Invalid language supplied. Supported languages: %s" % ','.join(lang_codes))

    @validator('include', whole=True)
    def include_search_params(cls, v):
        if not any(p in include_list for p in v):
            raise ValueError('include parameter must be one of: %s' % ', '.join(p for p in include_list))

    @validator('only', whole=True)
    def only_search_params(cls, v):
        if not any(p in only_list for p in v):
            raise ValueError('include parameter must be one of: %s' % ', '.join(p for p in unit_fields))


class UnitRequestFilters(BaseModel):

    include: List[str] = None
    only: List[str] = None

    @validator('include', whole=True)
    def include_search_params(cls, v):
        if not any(p in unit_foreign_fields for p in v):
            raise ValueError('include parameter must be one of: %s' % ', '.join(p for p in unit_foreign_fields))

    @validator('only', whole=True)
    def only_search_params(cls, v):
        if not any(p in unit_fields for p in v):
            raise ValueError('include parameter must be one of: %s' % ', '.join(p for p in unit_fields))
