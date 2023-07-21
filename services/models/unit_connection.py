from django.db import models

from .unit import Unit


class UnitConnection(models.Model):
    PHONE_OR_EMAIL_TYPE = 1
    LINK_TYPE = 2
    TOPICAL_TYPE = 3
    OTHER_INFO_TYPE = 4
    OPENING_HOURS_TYPE = 5
    SOCIAL_MEDIA_LINK_TYPE = 6
    OTHER_ADDRESS_TYPE = 7
    HIGHLIGHT_TYPE = 8
    ESERVICE_LINK_TYPE = 9
    PRICE_TYPE = 10

    SECTION_TYPES = (
        (PHONE_OR_EMAIL_TYPE, "PHONE_OR_EMAIL"),
        (LINK_TYPE, "LINK"),
        (TOPICAL_TYPE, "TOPICAL"),
        (OTHER_INFO_TYPE, "OTHER_INFO"),
        (OPENING_HOURS_TYPE, "OPENING_HOURS"),
        (SOCIAL_MEDIA_LINK_TYPE, "SOCIAL_MEDIA_LINK"),
        (OTHER_ADDRESS_TYPE, "OTHER_ADDRESS"),
        (HIGHLIGHT_TYPE, "HIGHLIGHT"),
        (ESERVICE_LINK_TYPE, "ESERVICE_LINK"),
        (PRICE_TYPE, "PRICE"),
    )

    unit = models.ForeignKey(
        Unit, db_index=True, related_name="connections", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=600)
    www = models.URLField(null=True, max_length=400)
    section_type = models.PositiveSmallIntegerField(choices=SECTION_TYPES, null=True)
    email = models.EmailField(max_length=100, null=True)
    phone = models.CharField(max_length=50, null=True)
    contact_person = models.CharField(max_length=80, null=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
