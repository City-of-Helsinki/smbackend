from django.db import models


class UnitAccessibilityProperty(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, related_name='accessibility_properties')
    variable = models.ForeignKey(AccessibilityVariable)
    value = models.CharField(max_length=100)
