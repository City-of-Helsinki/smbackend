from django.db import models

from .unit import Unit


class UnitAccessibilityShortcomings(models.Model):
    unit = models.OneToOneField(
        Unit,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="accessibility_shortcomings",
    )
    accessibility_shortcoming_count = models.JSONField(default=dict, null=True)
    accessibility_description = models.JSONField(default=list, null=True)
