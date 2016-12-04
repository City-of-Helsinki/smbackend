from django.conf import settings
from django.db import models
from services import models as services_models
from polymorphic.models import PolymorphicModel

class ObservableProperty(models.Model):
    """Specifies the detailed interpretation of observations.
    Includes the unit of measurement.

    Observations can only be made on units which have a service that
    is linked to an ObservableProperty.  For example, only units which
    are ice-skating fields can have observations with the property
    "ice condition" or something similar.

    """
    # TODO move back to sequential id field
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, null=False, blank=False, db_index=True)
    measurement_unit = models.CharField(max_length=20, null=True, blank=False)
    services = models.ManyToManyField(services_models.Service, related_name='observable_properties')
    observation_type = models.CharField(max_length=80, null=False, blank=False)
    def __str__(self):
        return "%s (%s)" % (self.name, self.id)
    def get_internal_value(self, value):
        if self.observation_type == 'observations.CategoricalObservation':
            return self.allowed_values.get(identifier=value)
        return value
    def get_external_value(self, value):
        return getattr(value, 'identifier')

class AllowedValue(models.Model):
    # Currently only works for categorical observations
    identifier = models.CharField(
        max_length=50, null=False, blank=False, db_index=True)
    quality = models.CharField(
        max_length=50, null=False, blank=False, db_index=True,
        default='unknown')
    name = models.CharField(
        max_length=100, null=False,
        blank=False, db_index=True)
    description = models.TextField(null=False, blank=False)
    property = models.ForeignKey(
        ObservableProperty,
        blank=False, null=False,
        related_name='allowed_values')
    class Meta:
        unique_together = (
            ('identifier', 'property'),)

class Observation(PolymorphicModel):
    """An observation is a measured/observed value of
    a property of a unit at a certain time.
    """
    time = models.DateTimeField(
        db_index=True,
        help_text='Exact time the observation was made')
    unit = models.ForeignKey(
        services_models.Unit, blank=False, null=False,
        help_text='The unit the observation is about',
        related_name='observation_history')
    units = models.ManyToManyField(services_models.Unit, through='UnitLatestObservation')
    property = models.ForeignKey(
        ObservableProperty,
        blank=False, null=False,
        help_text='The property observed')
    @staticmethod
    def get_internal_value(value):
        if self.property.allowed_values.count() == 0:
            return value
        return self.property.allowed_values.get(identifier=value)
    class Meta:
        ordering = ['-time']

class CategoricalObservation(Observation):
    value = models.ForeignKey(
        AllowedValue, blank=False, null=False,
        db_column='id',
        related_name='instances')
    @staticmethod
    def get_type():
        return 'categorical'

class ContinuousObservation(Observation):
    value = models.FloatField()
    @staticmethod
    def get_type():
        return 'continuous'

class DescriptiveObservation(Observation):
    value = models.TextField()
    def allowed_values(self):
        return self.property.allowed_values.all()
    @staticmethod
    def get_type():
        return 'descriptive'

class UnitLatestObservation(models.Model):
    unit = models.ForeignKey(
        services_models.Unit,
        null=False, blank=False,
        related_name='latest_observations')
    property = models.ForeignKey(
        ObservableProperty, null=False, blank=False)
    observation = models.ForeignKey(
        Observation, null=False, blank=False)
    class Meta:
        unique_together = (
            ('unit', 'property'),)
