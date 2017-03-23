"""
Models added only to support the v4 interface of the TPR API. Extends the previous models.py
"""
from django.contrib.gis.db import models
from django.db.models.query import QuerySet

from django.utils.encoding import python_2_unicode_compatible
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from django.conf import settings
from django.db.models import Q

from django.contrib.postgres.fields import HStoreField

from munigeo.models import AdministrativeDivision, Municipality
from munigeo.utils import get_default_srid

DEFAULT_LANG = settings.LANGUAGES[0][0]
PROJECTION_SRID = get_default_srid()

import django.db
from django.db.models.signals import pre_migrate
from django.dispatch import receiver
import sys

from .models import *


# TODO: When we get rid of the old model, this can be renamed as Service.
# This is named ServiceNode just so it won't conflict with Service.
class ServiceNode(MPTTModel):
    id = models.IntegerField(primary_key=True) # id of ontologytree
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')
    unit_count = models.PositiveIntegerField(null=True)
    keywords = models.ManyToManyField(Keyword)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    leaves = models.ManyToManyField("ServiceLeaf")

    objects = ServiceManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)


class ServiceLeaf(models.Model):
    id = models.IntegerField(primary_key=True) # id of ontologyword
    name = models.CharField(max_length=200, db_index=True)

    unit_count = models.PositiveIntegerField(null=True)
    keywords = models.ManyToManyField(Keyword)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

