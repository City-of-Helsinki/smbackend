from django.db import models

from .unit import Unit


class UnitIdentifier(models.Model):
    unit = models.ForeignKey(
        Unit, db_index=True, related_name="identifiers", on_delete=models.CASCADE
    )
    namespace = models.CharField(max_length=50)
    value = models.CharField(max_length=100)
