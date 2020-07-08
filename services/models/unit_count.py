from django.db import models
from munigeo.models import AdministrativeDivision, AdministrativeDivisionType

from . import Service, ServiceNode


class BaseUnitCount(models.Model):
    division_type = models.ForeignKey(AdministrativeDivisionType, null=False, on_delete=models.CASCADE)
    division = models.ForeignKey(AdministrativeDivision, null=True, db_index=True, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(null=False)

    class Meta:
        abstract = True


class ServiceNodeUnitCount(BaseUnitCount):
    service_node = models.ForeignKey(ServiceNode, null=False, db_index=True,
                                     related_name='unit_counts', on_delete=models.CASCADE)

    class Meta:
        unique_together = (('service_node', 'division'),)


class ServiceUnitCount(BaseUnitCount):
    service = models.ForeignKey(Service, null=False, db_index=True,
                                related_name='unit_counts', on_delete=models.CASCADE)

    class Meta:
        unique_together = (('service', 'division'),)
