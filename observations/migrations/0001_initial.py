# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AllowedValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('identifier', models.CharField(max_length=50, db_index=True)),
                ('quality', models.CharField(max_length=50, db_index=True, default='unknown')),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('name_fi', models.CharField(max_length=100, null=True, db_index=True)),
                ('name_sv', models.CharField(max_length=100, null=True, db_index=True)),
                ('name_en', models.CharField(max_length=100, null=True, db_index=True)),
                ('description', models.TextField()),
                ('description_fi', models.TextField(null=True)),
                ('description_sv', models.TextField(null=True)),
                ('description_en', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ObservableProperty',
            fields=[
                ('id', models.CharField(primary_key=True, max_length=50, serialize=False)),
                ('name', models.CharField(max_length=100, db_index=True)),
                ('measurement_unit', models.CharField(max_length=20, null=True)),
                ('observation_type', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('time', models.DateTimeField(db_index=True, help_text='Exact time the observation was made')),
            ],
            options={
                'ordering': ['-time'],
            },
        ),
        migrations.CreateModel(
            name='PluralityAuthToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('key', models.CharField(max_length=40, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UnitLatestObservation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserOrganization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
            ],
        ),
        migrations.CreateModel(
            name='CategoricalObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(primary_key=True, serialize=False, auto_created=True, parent_link=True, to='observations.Observation')),
            ],
            options={
                'abstract': False,
            },
            bases=('observations.observation',),
        ),
        migrations.CreateModel(
            name='ContinuousObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(primary_key=True, serialize=False, auto_created=True, parent_link=True, to='observations.Observation')),
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
                ('observation_ptr', models.OneToOneField(primary_key=True, serialize=False, auto_created=True, parent_link=True, to='observations.Observation')),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('observations.observation',),
        ),
    ]
