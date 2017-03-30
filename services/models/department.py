from django.db import models
from services.utils import get_translated


class Department(models.Model):
    uuid = models.UUIDField(db_index=True, editable=False)
    business_id = models.CharField(max_length=10)  # take into consideration intl. ids
    hierarchy_level = models.SmallIntegerField(null=True)
    name = models.CharField(max_length=200, db_index=True)
    object_identifier = models.CharField(max_length=20)

    # organization = models.ForeignKey(OrganizationV2)
    # organization_type = models.CharField(max_length=20)

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)
