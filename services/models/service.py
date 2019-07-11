from django.db import models
from services.utils import get_translated
from .keyword import Keyword


class Service(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)

    keywords = models.ManyToManyField(Keyword)

    period_enabled = models.BooleanField(default=True)
    clarification_enabled = models.BooleanField(default=True)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')
    root_service_node = models.ForeignKey('ServiceNode', null=True, related_name='related_services')

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

    class Meta:
        ordering = ['-pk']


class UnitServiceDetails(models.Model):
    unit = models.ForeignKey('Unit', db_index=True, related_name='service_details')
    service = models.ForeignKey('Service', db_index=True, related_name='unit_details')
    period_begin_year = models.PositiveSmallIntegerField(null=True)
    period_end_year = models.PositiveSmallIntegerField(null=True)
    clarification = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('period_begin_year', 'unit', 'service', 'clarification_fi')
