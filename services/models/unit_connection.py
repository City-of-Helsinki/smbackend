from django.db import models
from .unit import Unit


class UnitConnection(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, related_name='connections')
    type = models.IntegerField()
    name = models.CharField(max_length=400)
    www_url = models.URLField(null=True, max_length=400)
    section = models.CharField(max_length=20)
    contact_person = models.CharField(max_length=80, null=True)
    email = models.EmailField(max_length=100, null=True)
    phone = models.CharField(max_length=50, null=True)
    phone_mobile = models.CharField(max_length=50, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

