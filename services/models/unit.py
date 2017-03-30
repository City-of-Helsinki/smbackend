from django.contrib.gis.db import models
from django.contrib.postgres.fields import HStoreField

from munigeo.models import AdministrativeDivision, Municipality
from munigeo.utils import get_default_srid

from services.utils import get_translated
from .department import Department
from .organization import Organization
from .service import Service
from .service_tree_node import ServiceTreeNode
from .keyword import Keyword


PROJECTION_SRID = get_default_srid()


class UnitSearchManager(models.GeoManager):
    def get_queryset(self):
        qs = super(UnitSearchManager, self).get_queryset()
        if self.only_fields:
            qs = qs.only(*self.only_fields)
        if self.include_fields:
            for f in self.include_fields:
                qs = qs.prefetch_related(f)
        return qs


class Unit(models.Model):
    id = models.IntegerField(primary_key=True)
    data_source_url = models.URLField(null=True)
    name = models.CharField(max_length=200, db_index=True)
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
    picture_caption = models.CharField(max_length=200, null=True)

    origin_last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    service_tree_nodes = models.ManyToManyField("ServiceTreeNode", related_name='units')
    services = models.ManyToManyField("Service", related_name='units')
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
    root_servicenodes = models.CommaSeparatedIntegerField(max_length=50, null=True)

    objects = models.GeoManager()
    search_objects = UnitSearchManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

    def get_root_services(self):
        tree_ids = self.services.all().values_list('tree_id', flat=True).distinct()
        qs = Service.objects.filter(level=0).filter(tree_id__in=list(tree_ids))
        srv_list = qs.values_list('id', flat=True).distinct()
        return sorted(srv_list)

    def get_root_servitreenodes(self):
        tree_ids = self.service_tree_nodes.all().values_list('tree_id', flat=True).distinct()
        qs = ServiceTreeNode.objects.filter(level=0).filter(tree_id__in=list(tree_ids))
        srv_list = qs.values_list('id', flat=True).distinct()
        return sorted(srv_list)
