from django.db import models
from .unit import Unit

SECTION_TYPES = (
    (1, 'PHONE_OR_EMAIL'),
    (2, 'LINK'),
    (3, 'TOPICAL'),
    (4, 'OTHER_INFO'),
    (5, 'OPENING_HOURS'),
    (6, 'SOCIAL_MEDIA_LINK'),
    (7, 'OTHER_ADDRESS'),
    (8, 'HIGHLIGHT'),
    (9, 'ESERVICE_LINK'),
)


class UnitConnection(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, related_name='connections')
    name = models.CharField(max_length=400)
    www = models.URLField(null=True, max_length=400)
    section_type = models.PositiveSmallIntegerField(choices=SECTION_TYPES, null=True)
    email = models.EmailField(max_length=100, null=True)
    phone = models.CharField(max_length=50, null=True)
    contact_person = models.CharField(max_length=80, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
