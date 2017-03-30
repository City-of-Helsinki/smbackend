# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('observations', '0001_initial'),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userorganization',
            name='organization',
            field=models.ForeignKey(to='services.Organization'),
        ),
        migrations.AddField(
            model_name='userorganization',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='organization'),
        ),
        migrations.AddField(
            model_name='unitlatestobservation',
            name='observation',
            field=models.ForeignKey(to='observations.Observation'),
        ),
        migrations.AddField(
            model_name='unitlatestobservation',
            name='property',
            field=models.ForeignKey(to='observations.ObservableProperty'),
        ),
        migrations.AddField(
            model_name='unitlatestobservation',
            name='unit',
            field=models.ForeignKey(related_name='latest_observations', to='services.Unit'),
        ),
        migrations.AddField(
            model_name='pluralityauthtoken',
            name='user',
            field=models.ForeignKey(related_name='auth_tokens', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='observation',
            name='auth',
            field=models.ForeignKey(null=True, to='observations.PluralityAuthToken'),
        ),
        migrations.AddField(
            model_name='observation',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', related_name='polymorphic_observations.observation_set+', null=True, editable=False),
        ),
        migrations.AddField(
            model_name='observation',
            name='property',
            field=models.ForeignKey(to='observations.ObservableProperty', help_text='The property observed'),
        ),
        migrations.AddField(
            model_name='observation',
            name='unit',
            field=models.ForeignKey(to='services.Unit', help_text='The unit the observation is about', related_name='observation_history'),
        ),
        migrations.AddField(
            model_name='observation',
            name='units',
            field=models.ManyToManyField(to='services.Unit', through='observations.UnitLatestObservation'),
        ),
        migrations.AddField(
            model_name='observableproperty',
            name='services',
            field=models.ManyToManyField(related_name='observable_properties', to='services.Service'),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='property',
            field=models.ForeignKey(related_name='allowed_values', to='observations.ObservableProperty'),
        ),
        migrations.AlterUniqueTogether(
            name='unitlatestobservation',
            unique_together=set([('unit', 'property')]),
        ),
        migrations.AddField(
            model_name='categoricalobservation',
            name='value',
            field=models.ForeignKey(to='observations.AllowedValue', related_name='instances', db_column='id'),
        ),
        migrations.AlterUniqueTogether(
            name='allowedvalue',
            unique_together=set([('identifier', 'property')]),
        ),
    ]
