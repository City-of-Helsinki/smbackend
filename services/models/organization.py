from django.db import models
from services.utils import get_translated


class Organization(models.Model):
    uuid = models.UUIDField(unique=True, db_index=True, editable=False)

    business_id = models.CharField(max_length=10, null=True)
    organization_type = models.CharField(max_length=40)
    municipality_code = models.IntegerField(null=True, default=None)

    data_source_url = models.URLField(null=True, blank=True)

    # translated
    name = models.CharField(max_length=200, db_index=True, blank=True)
    abbr = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    street_address = models.CharField(max_length=100, null=True, blank=True)
    address_city = models.CharField(max_length=100, null=True, blank=True)
    address_postal_full = models.CharField(max_length=200, null=True, blank=True)
    www = models.CharField(max_length=200, null=True, blank=True)

    address_zip = models.CharField(max_length=10, null=True, blank=True)

    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=60, null=True, blank=True)

    object_identifier = models.CharField(max_length=20, null=True, blank=True)


    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)


