from django.core.validators import validate_comma_separated_integer_list
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_noop as _
from django.apps import apps

from munigeo.models import Municipality
from munigeo.utils import get_default_srid

from services.utils import get_translated
from .department import Department
from .keyword import Keyword

from django.contrib.postgres.operations import HStoreExtension
from django.contrib.postgres.fields import HStoreField
from django.db import migrations


PROJECTION_SRID = get_default_srid()
PROVIDER_TYPES = (
    (1, 'SELF_PRODUCED'),
    (2, 'MUNICIPALITY'),
    (3, 'ASSOCIATION'),
    (4, 'PRIVATE_COMPANY'),
    (5, 'OTHER_PRODUCTION_METHOD'),
    (6, 'PURCHASED_SERVICE'),
    (7, 'UNKNOWN_PRODUCTION_METHOD'),
    (8, 'CONTRACT_SCHOOL'),
    (9, 'SUPPORTED_OPERATIONS'),
    (10, 'PAYMENT_COMMITMENT'),
    (11, 'VOUCHER_SERVICE'),
)

ORGANIZER_TYPES = (
    (0, 'ASSOCIATION'),
    (1, 'FOUNDATION'),
    (2, 'GOVERNMENT'),
    (3, 'GOVERNMENTAL_COMPANY'),
    (4, 'JOINT_MUNICIPAL_AUTHORITY'),
    (5, 'MUNICIPAL_ENTERPRISE_GROUP'),
    (6, 'MUNICIPALITY'),
    (7, 'MUNICIPALLY_OWNED_COMPANY'),
    (8, 'ORGANIZATION'),
    (9, 'OTHER_REGIONAL_COOPERATION_ORGANIZATION'),
    (10, 'PRIVATE_ENTERPRISE'),
    (11, 'UNKNOWN'),
)

CONTRACT_TYPES = (
    (0, _('contract_school')),
    (1, _('municipal_service')),
    (2, _('private_service')),
    (3, _('purchased_service')),
    (4, _('service_by_joint_municipal_authority')),
    (5, _('service_by_municipal_group_entity')),
    (6, _('service_by_municipally_owned_company')),
    (7, _('service_by_other_municipality')),
    (8, _('service_by_regional_cooperation_organization')),
    (9, _('state_service')),
    (10, _('supported_operations')),
    (11, _('voucher_service'))
)


_unit_related_fields = set()
def get_unit_related_fields():
    global _unit_related_fields
    if len(_unit_related_fields) > 0:
        return _unit_related_fields
    Unit = apps.get_model(app_label='services', model_name='Unit')
    for f in Unit._meta.get_fields():
        if f.is_relation:
            _unit_related_fields.add(f.name)
    return _unit_related_fields


class UnitSearchManager(models.GeoManager):
    def get_queryset(self):
        qs = super(UnitSearchManager, self).get_queryset()
        if self.only_fields:
            qs = qs.only(*self.only_fields)
        if self.include_fields:
            unit_related_fields = get_unit_related_fields()
            for f in self.include_fields:
                if f in unit_related_fields:
                    qs = qs.prefetch_related(f)
        return qs.filter(public=True)


class Unit(models.Model):
    id = models.IntegerField(primary_key=True)

    public = models.BooleanField(null=False, default=True)

    location = models.PointField(null=True, srid=PROJECTION_SRID)  # lat, lng?
    geometry = models.GeometryField(srid=PROJECTION_SRID, null=True)
    department = models.ForeignKey(Department, null=True)
    root_department = models.ForeignKey(Department, null=True, related_name='descendant_units')

    organizer_type = models.PositiveSmallIntegerField(choices=ORGANIZER_TYPES, null=True)
    organizer_name = models.CharField(max_length=150, null=True)
    organizer_business_id = models.CharField(max_length=10, null=True)

    provider_type = models.PositiveSmallIntegerField(choices=PROVIDER_TYPES, null=True)
    contract_type = models.PositiveSmallIntegerField(choices=CONTRACT_TYPES, null=True)

    picture_url = models.URLField(max_length=250, null=True)
    picture_entrance_url = models.URLField(max_length=500, null=True)
    streetview_entrance_url = models.URLField(max_length=500, null=True)

    description = models.TextField(null=True)
    short_description = models.TextField(null=True)
    name = models.CharField(max_length=200, db_index=True)
    street_address = models.CharField(max_length=100, null=True)

    www = models.URLField(max_length=400, null=True)
    address_postal_full = models.CharField(max_length=100, null=True)
    call_charge_info = models.CharField(max_length=100, null=True)

    picture_caption = models.TextField(null=True)

    phone = models.CharField(max_length=120, null=True)
    fax = models.CharField(max_length=50, null=True)
    email = models.EmailField(max_length=100, null=True)
    accessibility_phone = models.CharField(max_length=50, null=True)
    accessibility_email = models.EmailField(max_length=100, null=True)
    accessibility_www = models.URLField(max_length=400, null=True)

    created_time = models.DateTimeField(null=True)  # ASK API: are these UTC? no Z in output

    municipality = models.ForeignKey(Municipality, null=True, db_index=True)
    address_zip = models.CharField(max_length=10, null=True)

    data_source = models.CharField(max_length=30, null=True)
    extensions = HStoreField(null=True)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    service_nodes = models.ManyToManyField("ServiceNode", related_name='units')
    services = models.ManyToManyField("Service", related_name='units', through='UnitServiceDetails')
    keywords = models.ManyToManyField(Keyword)

    connection_hash = models.CharField(max_length=40, null=True,
                                       help_text='Automatically generated hash of connection info')
    accessibility_property_hash = models.CharField(
        max_length=40, null=True, help_text='Automatically generated hash of accessibility property info')
    identifier_hash = models.CharField(max_length=40, null=True,
                                       help_text='Automatically generated hash of other identifiers')
    service_details_hash = models.CharField(max_length=40, null=True)

    accessibility_viewpoints = JSONField(default="{}", null=True)

    # Cached fields for better performance
    root_service_nodes = models.CharField(max_length=50, null=True,
                                          validators=[validate_comma_separated_integer_list])

    objects = models.GeoManager()
    search_objects = UnitSearchManager()

    class Meta:
        ordering = ['-pk']

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

    def get_root_service_nodes(self):
        from .service_node import ServiceNode

        tree_ids = self.service_nodes.all().values_list('tree_id', flat=True).distinct()
        qs = ServiceNode.objects.filter(level=0).filter(tree_id__in=list(tree_ids))
        service_node_list = qs.values_list('id', flat=True).distinct()
        return sorted(service_node_list)


class Migration(migrations.Migration):
    ...

    operations = [
        HStoreExtension(),
        ...
    ]
