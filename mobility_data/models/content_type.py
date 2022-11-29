import uuid

from django.contrib.gis.db import models


class BaseType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=64, null=True, unique=True)
    description = models.TextField(
        null=True, verbose_name="Optional description of the content type."
    )

    class Meta:
        abstract = True
        ordering = ["id"]

    def __str__(self):
        return self.name


class ContentType(BaseType):

    type_name = models.CharField(max_length=3, null=True)


class GroupType(BaseType):

    type_name = models.CharField(max_length=3, null=True)
