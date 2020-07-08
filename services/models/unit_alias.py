from django.db import models

from .unit import Unit


class UnitAlias(models.Model):
    first = models.ForeignKey(Unit, related_name="aliases", on_delete=models.CASCADE)

    # Not a foreign key, might need
    # to reference nonexistent models
    second = models.IntegerField(db_index=True, unique=True)
