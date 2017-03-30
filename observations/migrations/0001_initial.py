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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('identifier', models.CharField(db_index=True, max_length=50)),
                ('quality', models.CharField(db_index=True, default='unknown', max_length=50)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('name_fi', models.CharField(db_index=True, null=True, max_length=100)),
                ('name_sv', models.CharField(db_index=True, null=True, max_length=100)),
                ('name_en', models.CharField(db_index=True, null=True, max_length=100)),
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
                ('name', models.CharField(db_index=True, max_length=100)),
                ('measurement_unit', models.CharField(null=True, max_length=20)),
                ('observation_type', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('time', models.DateTimeField(db_index=True, help_text='Exact time the observation was made')),
            ],
            options={
                'ordering': ['-time'],
            },
        ),
        migrations.CreateModel(
            name='PluralityAuthToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('key', models.CharField(db_index=True, max_length=40)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserOrganization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
            ],
        ),
        migrations.CreateModel(
            name='CategoricalObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(serialize=False, primary_key=True, to='observations.Observation', auto_created=True, parent_link=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('observations.observation',),
        ),
        migrations.CreateModel(
            name='ContinuousObservation',
            fields=[
                ('observation_ptr', models.OneToOneField(serialize=False, primary_key=True, to='observations.Observation', auto_created=True, parent_link=True)),
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
                ('observation_ptr', models.OneToOneField(serialize=False, primary_key=True, to='observations.Observation', auto_created=True, parent_link=True)),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('observations.observation',),
        ),
    ]
