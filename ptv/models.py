from django.db import models

from services.models import Service, Unit


class UnitPTVIdentifier(models.Model):
    id = models.UUIDField(primary_key=True)
    unit = models.OneToOneField(
        Unit, on_delete=models.CASCADE, related_name="ptv_id", blank=True, null=True
    )


class ServicePTVIdentifier(models.Model):
    id = models.UUIDField(primary_key=True)
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="ptv_ids", blank=True, null=True
    )
