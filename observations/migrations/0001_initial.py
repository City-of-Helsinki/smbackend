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
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('identifier', models.CharField(max_length=50, db_index=True)),
                ('quality', models.CharField(default='unknown', max_length=50, db_index=True)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('name_fi', models.CharField(max_length=100, db_index=True, null=True)),
                ('name_sv', models.CharField(max_length=100, db_index=True, null=True)),
                ('name_en', models.CharField(max_length=100, db_index=True, null=True)),
                ('description', models.TextField()),
                ('description_fi', models.TextField(null=True)),
                ('description_sv', models.TextField(null=True)),
                ('description_en', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ObservableProperty',
            fields=[
                ('id', models.CharField(serialize=False, primary_key=True, max_length=50)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('measurement_unit', models.CharField(max_length=20, null=True)),
                ('observation_type', models.CharField(max_length=80)),
                ('services', models.ManyToManyField(to='services.Service', related_name='observable_properties')),
            ],
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('time', models.DateTimeField(help_text='Exact time the observation was made', db_index=True)),
            ],
            options={
                'ordering': ['-time'],
            },
        ),
        migrations.CreateModel(
            name='CategoricalObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(serialize=False, to='observations.Observation', primary_key=True, auto_created=True, parent_link=True)),
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
                ('observation_ptr', models.OneToOneField(serialize=False, to='observations.Observation', primary_key=True, auto_created=True, parent_link=True)),
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
                ('observation_ptr', models.OneToOneField(serialize=False, to='observations.Observation', primary_key=True, auto_created=True, parent_link=True)),
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
            field=models.ForeignKey(to='contenttypes.ContentType', related_name='polymorphic_observations.observation_set+', editable=False, null=True),
        ),
        migrations.AddField(
            model_name='observation',
            name='property',
            field=models.ForeignKey(to='observations.ObservableProperty', help_text='The property observed'),
        ),
        migrations.AddField(
            model_name='observation',
            name='unit',
            field=models.ForeignKey(to='services.Unit', help_text='The unit the observation is about', related_name='observations'),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='property',
            field=models.ForeignKey(related_name='allowed_values', to='observations.ObservableProperty'),
        ),
        migrations.AlterUniqueTogether(
            name='allowedvalue',
            unique_together=set([('identifier', 'property')]),
        ),
    ]
