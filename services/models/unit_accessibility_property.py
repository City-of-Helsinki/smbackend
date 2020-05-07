from django.db import models
from .unit import Unit
from .accessibility_variable import AccessibilityVariable


class UnitAccessibilityProperty(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, related_name='accessibility_properties', on_delete=models.CASCADE)
    variable = models.ForeignKey(AccessibilityVariable, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
