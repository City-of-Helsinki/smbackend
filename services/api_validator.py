import re
from typing import List, Tuple
from uuid import UUID

from pydantic import BaseModel, validator

from smbackend import settings


class RequestFilters(BaseModel):
    id: List[int] = []
    municipality: List[str] = []
    department_or_municipality: List[UUID] = None
    provider_type: List[int] = None
    provider_type__not: List[int] = None
    level: List[str] = []
    service_node: List[int] = None
    exclude_service_nodes: List[int] = None
    service: List[int] = None
    division: List[str] = []
    lat: List[float] = None
    lon: List[float] = None
    distance: List[float] = None
    bbox_srid: str = None
    bbox: Tuple[str, int] = None
    category: List[str] = None
    maintenance_organization: List[int] = None
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

    @validator('type')
    def check_type(cls, v):
        types = ['service_node', 'service', 'unit', 'address']
        if not any(t in types for t in v):
            raise ValueError('type must be one of: service_node, service, unit, address')
