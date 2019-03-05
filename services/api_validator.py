import re
from typing import List, Tuple
from uuid import UUID

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

    id: List[int] = None
    municipality: List[str] = None
    department_or_municipality: List[UUID] = None
    provider_type: List[int] = None
    provider_type__not: List[int] = None
    level: List[str] = None
    service_node: List[int] = None
    exclude_service_nodes: List[int] = None
    service: List[int] = None
    division: List[str] = None
    lat: List[float] = None
    lon: List[float] = None
    distance: List[float] = None
    bbox_srid: List[str] = None
    bbox: Tuple[int, int, int, int] = None
    category: List[str] = None
    maintenance_organization: List[int] = None
    type: List[str] = None
    page: List[int] = None
    geometry: List[bool] = None

    @validator('municipality', whole=True)
    def check_municipality(cls, v):
        for m in v:
            if not m.startswith('ocd-division') and len(re.findall(r"[\d,.]", m)) > 0:
                raise ValueError("'%s' not a suitable value for municipality'" % m)

    @validator('distance', 'lat', 'lon', whole=True)
    def check_single_value(cls, v):
        if len(v) > 1:
            raise ValueError('only one value accepted')

    @validator('distance')
    def check_positive(cls, v):
        if not v > 0:
            raise ValueError('distance must be a positive float number')

    @validator('level', whole=True)
    def check_level(cls, v):
        levels = list(settings.LEVELS.keys())
        levels.append('all')
        if len(v) > 1:
            raise ValueError('single value expected')
        if v[0] not in levels:
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


class SearchRequestFilters(BaseModel):

    include: List[str] = None
    only: List[str] = None

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
