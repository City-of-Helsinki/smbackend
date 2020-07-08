from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from munigeo.models import Municipality

from services.utils import get_translated

from .hierarchy import CustomTreeManager


class Department(MPTTModel):
    uuid = models.UUIDField(db_index=True, editable=False, unique=True)
    business_id = models.CharField(max_length=10)  # take into consideration intl. ids

    parent = TreeForeignKey(
        "self", null=True, related_name="children", on_delete=models.CASCADE
    )

    # translateable group here
    name = models.CharField(max_length=200, db_index=True)
    abbr = models.CharField(max_length=50, db_index=True, null=True)
    street_address = models.CharField(max_length=100, null=True)
    address_city = models.CharField(max_length=100, null=True)
    address_postal_full = models.CharField(max_length=200, null=True)
    www = models.CharField(max_length=200, null=True)

    phone = models.CharField(max_length=30, null=True)
    address_zip = models.CharField(max_length=10, null=True)
    oid = models.TextField(null=True)

    organization_type = models.CharField(max_length=50, null=True)

    municipality = models.ForeignKey(
        Municipality, null=True, db_index=True, on_delete=models.CASCADE
    )

    objects = CustomTreeManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, "name"), self.id)

    # This is used for unit indexing
    def top_departments(self, depth=3):
        ancestors = self.get_ancestors(include_self=True).filter(level__lt=depth)
        return " ".join([anc.name for anc in ancestors])
