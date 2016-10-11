from django.conf import settings
from django.db import models
from services import models as services_models

class ObservableProperty(models.Model):
    """Specifies the detailed interpretation of observations.
    Includes the unit of measurement.

    Observations can only be made on units which have a service that
    is linked to an ObservableProperty.  For example, only units which
    are ice-skating fields can have observations with the property
    "ice condition" or something similar.

    """
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, null=False, blank=False, db_index=True)
    measurement_unit = models.CharField(max_length=20, null=True, blank=False)
    services = models.ManyToManyField(services_models.Service, related_name='observable_properties')
    observation_type = models.CharField(max_length=80, null=False, blank=False)

class AllowedValue(models.Model):
    internal_value = models.SmallIntegerField()
    identifier = models.CharField(
        max_length=50, null=False, blank=False)
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
            ('identifier', 'property'),
            ('internal_value', 'property'),)

class Observation(models.Model):
    """An observation is a measured/observed value of
    a property of a unit at a certain time.
    """
    time = models.DateTimeField(
        db_index=True,
        help_text='Exact time the observation was made')
    unit = models.ForeignKey(
        services_models.Unit, blank=False, null=False,
        help_text='The unit the observation is about')
    property = models.ForeignKey(
        ObservableProperty,
        blank=False, null=False,
        help_text='The property observed')

class CategoricalObservation(Observation):
    value = models.SmallIntegerField()
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
