from django.db import models

from services.models import Unit


class UnitPTVIdentifier(models.Model):
    id = models.UUIDField(primary_key=True)
    unit = models.OneToOneField(
        Unit, on_delete=models.CASCADE, related_name="ptv_id", blank=True, null=True
    )
