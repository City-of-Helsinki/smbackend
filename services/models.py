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

@receiver(pre_migrate, sender=sys.modules[__name__])
def setup_postgres_hstore(sender, **kwargs):
    """
    Always create PostgreSQL HSTORE extension if it doesn't already exist
    on the database before syncing the database.
    Requires PostgreSQL 9.1 or newer.
    """
    cursor = django.db.connection.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS hstore")

def get_translated(obj, attr):
    key = "%s_%s" % (attr, DEFAULT_LANG)
    val = getattr(obj, key, None)
    if not val:
        val = getattr(obj, attr)
    return val


@python_2_unicode_compatible
class Keyword(models.Model):
    language = models.CharField(max_length=10, choices=settings.LANGUAGES, db_index=True)
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = (('language', 'name'),)

    def __str__(self):
        return "%s (%s)" % (self.name, self.language)


class ServiceQuerySet(QuerySet):
    def by_ancestor(self, ancestor):
        manager = self.model.objects
        max_level = manager.determine_max_level()
        qs = Q()
        # Construct an OR'd queryset for each level of parenthood.
        for i in range(max_level):
            key = '__'.join(['parent'] * (i + 1))
            qs |= Q(**{key: ancestor})
        return self.filter(qs)

class ServiceManager(TreeManager):
    def get_queryset(self):
        return ServiceQuerySet(self.model, using=self._db)

    def determine_max_level(self):
        if hasattr(self, '_max_level'):
            return self._max_level
        qs = self.all().order_by('-level')
        if qs.count():
            self._max_level = qs[0].level
        else:
            # Harrison-Stetson method
            self._max_level = 10
        return self._max_level

@python_2_unicode_compatible
class Service(MPTTModel):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')
    unit_count = models.PositiveIntegerField()
    keywords = models.ManyToManyField(Keyword)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    identical_to = models.ForeignKey('self', null=True, related_name='duplicates')

    objects = ServiceManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

    def get_unit_count(self):
        srv_list = set(Service.objects.all().by_ancestor(self).values_list('id', flat=True))
        srv_list.add(self.id)
        return Unit.objects.filter(services__in=list(srv_list)).distinct().count()


@python_2_unicode_compatible
class Organization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    data_source_url = models.URLField(max_length=200)

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

@python_2_unicode_compatible
class Department(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    abbr = models.CharField(max_length=20, db_index=True)
    organization = models.ForeignKey(Organization)

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

class UnitSearchManager(models.GeoManager):
    def get_queryset(self):
        qs = super(UnitSearchManager, self).get_queryset()
        if self.only_fields:
            qs = qs.only(*self.only_fields)
        if self.include_fields:
            for f in self.include_fields:
                qs = qs.prefetch_related(f)
        return qs

@python_2_unicode_compatible
class Unit(models.Model):
    id = models.IntegerField(primary_key=True)
    data_source_url = models.URLField(null=True)
    name = models.CharField(max_length=210, db_index=True)
    description = models.TextField(null=True)

    provider_type = models.IntegerField()

    location = models.PointField(null=True, srid=PROJECTION_SRID)
    geometry = models.GeometryField(srid=PROJECTION_SRID, null=True)
    department = models.ForeignKey(Department, null=True)
    organization = models.ForeignKey(Organization)

    street_address = models.CharField(max_length=100, null=True)
    address_zip = models.CharField(max_length=10, null=True)
    phone = models.CharField(max_length=50, null=True)
    email = models.EmailField(max_length=100, null=True)
    www_url = models.URLField(max_length=400, null=True)
    address_postal_full = models.CharField(max_length=100, null=True)
    municipality = models.ForeignKey(Municipality, null=True, db_index=True)

    data_source = models.CharField(max_length=20, null=True)
    extensions = HStoreField(null=True)

    picture_url = models.URLField(max_length=250, null=True)
    picture_caption = models.CharField(max_length=250, null=True)

    origin_last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    services = models.ManyToManyField(Service, related_name='units')
    divisions = models.ManyToManyField(AdministrativeDivision)
    keywords = models.ManyToManyField(Keyword)

    connection_hash = models.CharField(max_length=40, null=True,
        help_text='Automatically generated hash of connection info')
    accessibility_property_hash = models.CharField(max_length=40, null=True,
        help_text='Automatically generated hash of accessibility property info')
    identifier_hash = models.CharField(max_length=40, null=True,
        help_text='Automatically generated hash of other identifiers')

    # Cached fields for better performance
    root_services = models.CommaSeparatedIntegerField(max_length=50, null=True)

    objects = models.GeoManager()
    search_objects = UnitSearchManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

    def get_root_services(self):
        tree_ids = self.services.all().values_list('tree_id', flat=True).distinct()
        qs = Service.objects.filter(level=0).filter(tree_id__in=list(tree_ids))
        srv_list = qs.values_list('id', flat=True).distinct()
        return sorted(srv_list)


@python_2_unicode_compatible
class UnitIdentifier(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, related_name='identifiers')
    namespace = models.CharField(max_length=50)
    value = models.CharField(max_length=100)


@python_2_unicode_compatible
class AccessibilityVariable(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class UnitAccessibilityProperty(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, related_name='accessibility_properties')
    variable = models.ForeignKey(AccessibilityVariable)
    value = models.CharField(max_length=100)


@python_2_unicode_compatible
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

@python_2_unicode_compatible
class UnitAlias(models.Model):
    first = models.ForeignKey(Unit, related_name='aliases')

    # Not a foreign key, might need
    # to reference nonexistent models
    second = models.IntegerField(db_index=True, unique=True)
