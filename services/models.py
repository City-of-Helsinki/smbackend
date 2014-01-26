from six import with_metaclass
from django.contrib.gis.db import models
from django.utils.encoding import python_2_unicode_compatible
from mptt.models import MPTTModel, MPTTModelBase, TreeForeignKey
from mptt.managers import TreeManager
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone

DEFAULT_LANG = settings.LANGUAGES[0][0]

def get_translated(obj, attr):
    key = "%s_%s" % (attr, DEFAULT_LANG)
    val = getattr(obj, key, None)
    if not val:
        val = getattr(obj, attr)
    return val

@python_2_unicode_compatible
class Service(MPTTModel):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

@python_2_unicode_compatible
class Organization(models.Model):
    id = models.IntegerField(max_length=20, primary_key=True)
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

@python_2_unicode_compatible
class Unit(models.Model):
    id = models.IntegerField(primary_key=True)
    data_source_url = models.URLField(null=True)
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(null=True)

    provider_type = models.IntegerField()

    location = models.PointField(null=True, srid=settings.PROJECTION_SRID)
    department = models.ForeignKey(Department, null=True)
    organization = models.ForeignKey(Organization)

    street_address = models.CharField(max_length=100, null=True)
    address_zip = models.CharField(max_length=10, null=True)
    phone = models.CharField(max_length=30, null=True)
    email = models.EmailField(max_length=50, null=True)
    www_url = models.URLField(max_length=400, null=True)
    address_postal_full = models.CharField(max_length=100, null=True)

    picture_url = models.URLField(max_length=200, null=True)
    picture_caption = models.CharField(max_length=200, null=True)

    origin_last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    services = models.ManyToManyField(Service)

    objects = models.Manager()
    geo_objects = models.GeoManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)
