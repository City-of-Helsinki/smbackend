import uuid

from django.contrib.gis.db import models


class BaseType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    type_name = models.CharField(max_length=64, null=True, unique=True)
    name = models.CharField(max_length=128, null=True)
    description = models.TextField(
        null=True, verbose_name="Optional description of the content type."
    )

    class Meta:
        abstract = True
        ordering = ["type_name"]

    def __str__(self):
        return self.type_name


class ContentType(BaseType):

    pass


class GroupType(BaseType):

    pass
