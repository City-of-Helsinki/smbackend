# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('services', '0008_auto_20161106_1125'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllowedValue',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('internal_value', models.SmallIntegerField()),
                ('identifier', models.CharField(db_index=True, max_length=50)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ObservableProperty',
            fields=[
                ('id', models.CharField(serialize=False, primary_key=True, max_length=50)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('measurement_unit', models.CharField(null=True, max_length=20)),
                ('observation_type', models.CharField(max_length=80)),
                ('services', models.ManyToManyField(related_name='observable_properties', to='services.Service')),
            ],
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('time', models.DateTimeField(help_text='Exact time the observation was made', db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CategoricalObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(serialize=False, to='observations.Observation', primary_key=True, parent_link=True, auto_created=True)),
                ('value', models.SmallIntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('observations.observation',),
        ),
        migrations.CreateModel(
            name='ContinuousObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(serialize=False, to='observations.Observation', primary_key=True, parent_link=True, auto_created=True)),
                ('value', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
            bases=('observations.observation',),
        ),
        migrations.CreateModel(
            name='DescriptiveObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(serialize=False, to='observations.Observation', primary_key=True, parent_link=True, auto_created=True)),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('observations.observation',),
        ),
        migrations.AddField(
            model_name='observation',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, related_name='polymorphic_observations.observation_set+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='observation',
            name='property',
            field=models.ForeignKey(to='observations.ObservableProperty', help_text='The property observed'),
        ),
        migrations.AddField(
            model_name='observation',
            name='unit',
            field=models.ForeignKey(to='services.Unit', help_text='The unit the observation is about'),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='property',
            field=models.ForeignKey(to='observations.ObservableProperty', related_name='allowed_values'),
        ),
        migrations.AlterUniqueTogether(
            name='allowedvalue',
            unique_together=set([('identifier', 'property'), ('internal_value', 'property')]),
        ),
    ]
