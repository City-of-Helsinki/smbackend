from six import with_metaclass
from django.contrib.gis.db import models
from django.utils.encoding import python_2_unicode_compatible
from linguo.models import MultilingualModel, MultilingualModelBase
from linguo.managers import MultilingualManager
from mptt.models import MPTTModel, MPTTModelBase, TreeForeignKey
from mptt.managers import TreeManager

class ServiceMeta(MultilingualModelBase, MPTTModelBase):
    pass

@python_2_unicode_compatible
class Service(with_metaclass(ServiceMeta, MultilingualModel, MPTTModel)):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')

    class Meta:
        translate = ('name',)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Organization(with_metaclass(MultilingualModelBase, MultilingualModel)):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    data_source_url = models.URLField(max_length=200)

    objects = MultilingualManager()

    class Meta:
        translate = ('name',)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Department(with_metaclass(MultilingualModelBase, MultilingualModel)):
    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    abbr = models.CharField(max_length=20, db_index=True)
    organization = models.ForeignKey(Organization)

    objects = MultilingualManager()

    class Meta:
        translate = ('name',)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Unit(with_metaclass(MultilingualModelBase, MultilingualModel)):
    id = models.IntegerField(primary_key=True)
    data_source_url = models.URLField(null=True)
    name = models.CharField(max_length=200, db_index=True)
    location = models.PointField(null=True)
    department = models.ForeignKey(Department)
    organization = models.ForeignKey(Organization)

    street_address = models.CharField(max_length=100, null=True)
    address_zip = models.CharField(max_length=10, null=True)
    phone = models.CharField(max_length=30, null=True)
    email = models.CharField(max_length=50, null=True)
    www_url = models.URLField(max_length=200, null=True)
    address_postal_full = models.CharField(max_length=50, null=True)

    services = models.ManyToManyField(Service)

    objects = MultilingualManager()

    class Meta:
        translate = ('name',)

    def __str__(self):
        return self.name
