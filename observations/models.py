from django.conf import settings
from django.db import models
from django.apps import apps
from django.utils.translation import ugettext_lazy as _
from services import models as services_models
from polymorphic.models import PolymorphicModel
import binascii
import os
from rest_framework import exceptions

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
    services = models.ManyToManyField(services_models.OntologyWord, related_name='observable_properties')
    observation_type = models.CharField(max_length=80, null=False, blank=False)
    def __str__(self):
        return "%s (%s)" % (self.name, self.id)
    def get_observation_model(self):
        return apps.get_model(self.observation_type)
    def get_observation_type(self):
        return self.get_observation_model().get_type()
    def create_observation(self, **validated_data):
        return self.get_observation_model().objects.create(**validated_data)
    def get_internal_value(self, value):
        return self.get_observation_model().get_internal_value(self, value)

class AllowedValue(models.Model):
    # Currently only works for categorical observations
    identifier = models.CharField(
        max_length=50, null=True, blank=False, db_index=True)
    quality = models.CharField(
        max_length=50, null=True, blank=False, db_index=True,
        default='unknown')
    name = models.CharField(
        max_length=100, null=True,
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
    value = models.ForeignKey(
        AllowedValue, blank=False, null=True,
        related_name='instances')
    time = models.DateTimeField(
        db_index=True,
        help_text='Exact time the observation was made')
    unit = models.ForeignKey(
        services_models.Unit, blank=False, null=False,
        help_text='The unit the observation is about',
        related_name='observation_history')
    units = models.ManyToManyField(services_models.Unit, through='UnitLatestObservation')
    auth = models.ForeignKey(
        'PluralityAuthToken', null=True)
    property = models.ForeignKey(
        ObservableProperty,
        blank=False, null=False,
        help_text='The property observed')
    class Meta:
        ordering = ['-time']

class CategoricalObservation(Observation):
    def get_external_value(self):
        return self.value.identifier

    @staticmethod
    def get_type():
        return 'categorical'
    @staticmethod
    def get_internal_value(oproperty, value):
        if value is None:
            return None
        return oproperty.allowed_values.get(identifier=value)


class DescriptiveObservation(Observation):
    def get_external_value(self):
        return self.value
    @staticmethod
    def get_type():
        return 'descriptive'
    @staticmethod
    def get_internal_value(oproperty, value):
        return AllowedValue.objects.create(property=oproperty, **value)

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

import rest_framework.authtoken.models
import rest_framework.authentication

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
class PluralityAuthToken(models.Model):
    """
    A token class which can have multiple active tokens per user.
    """
    key = models.CharField(max_length=40, primary_key=False, db_index=True)
    user = models.ForeignKey(AUTH_USER_MODEL, related_name='auth_tokens', null=False)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        # Work around for a bug in Django:
        # https://code.djangoproject.com/ticket/19422
        #
        # Also see corresponding ticket:
        # https://github.com/tomchristie/django-rest-framework/issues/705
        abstract = 'rest_framework.authtoken' not in settings.INSTALLED_APPS

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(PluralityAuthToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key

class PluralityTokenAuthentication(rest_framework.authentication.TokenAuthentication):
    model = PluralityAuthToken
    def authenticate_credentials(self, key):
        user, token = super(PluralityTokenAuthentication, self).authenticate_credentials(key)
        if not token.active:
            raise exceptions.AuthenticationFailed(_('Token inactive or deleted.'))
        return (token.user, token)

class UserOrganization(models.Model):
    organization = models.ForeignKey(services_models.Organization)
    user = models.OneToOneField(AUTH_USER_MODEL, related_name='organization', null=False)
