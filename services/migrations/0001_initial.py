# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessibilityVariable',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.CharField(serialize=False, primary_key=True, max_length=20)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_sv', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_en', models.CharField(max_length=200, null=True, db_index=True)),
                ('abbr', models.CharField(db_index=True, max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('language', models.CharField(choices=[('fi', 'Finnish'), ('sv', 'Swedish'), ('en', 'English')], db_index=True, max_length=10)),
                ('name', models.CharField(db_index=True, max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True, max_length=20)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_sv', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_en', models.CharField(max_length=200, null=True, db_index=True)),
                ('data_source_url', models.URLField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_sv', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_en', models.CharField(max_length=200, null=True, db_index=True)),
                ('unit_count', models.PositiveIntegerField()),
                ('last_modified_time', models.DateTimeField(help_text='Time of last modification', db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('identical_to', models.ForeignKey(to='services.Service', related_name='duplicates', null=True)),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
                ('parent', mptt.fields.TreeForeignKey(to='services.Service', related_name='children', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('data_source_url', models.URLField(null=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_sv', models.CharField(max_length=200, null=True, db_index=True)),
                ('name_en', models.CharField(max_length=200, null=True, db_index=True)),
                ('description', models.TextField(null=True)),
                ('description_fi', models.TextField(null=True)),
                ('description_sv', models.TextField(null=True)),
                ('description_en', models.TextField(null=True)),
                ('provider_type', models.IntegerField()),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=3067, null=True)),
                ('street_address', models.CharField(max_length=100, null=True)),
                ('street_address_fi', models.CharField(max_length=100, null=True)),
                ('street_address_sv', models.CharField(max_length=100, null=True)),
                ('street_address_en', models.CharField(max_length=100, null=True)),
                ('address_zip', models.CharField(max_length=10, null=True)),
                ('phone', models.CharField(max_length=30, null=True)),
                ('email', models.EmailField(max_length=100, null=True)),
                ('www_url', models.URLField(max_length=400, null=True)),
                ('www_url_fi', models.URLField(max_length=400, null=True)),
                ('www_url_sv', models.URLField(max_length=400, null=True)),
                ('www_url_en', models.URLField(max_length=400, null=True)),
                ('address_postal_full', models.CharField(max_length=100, null=True)),
                ('picture_url', models.URLField(null=True)),
                ('picture_caption', models.CharField(max_length=200, null=True)),
                ('picture_caption_fi', models.CharField(max_length=200, null=True)),
                ('picture_caption_sv', models.CharField(max_length=200, null=True)),
                ('picture_caption_en', models.CharField(max_length=200, null=True)),
                ('origin_last_modified_time', models.DateTimeField(help_text='Time of last modification', db_index=True)),
                ('connection_hash', models.CharField(help_text='Automatically generated hash of connection info', max_length=40, null=True)),
                ('accessibility_property_hash', models.CharField(help_text='Automatically generated hash of accessibility property info', max_length=40, null=True)),
                ('root_services', models.CommaSeparatedIntegerField(max_length=50, null=True)),
                ('department', models.ForeignKey(to='services.Department', null=True)),
                ('divisions', models.ManyToManyField(to='munigeo.AdministrativeDivision')),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
                ('municipality', models.ForeignKey(to='munigeo.Municipality', null=True)),
                ('organization', models.ForeignKey(to='services.Organization')),
                ('services', models.ManyToManyField(to='services.Service')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitAccessibilityProperty',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('value', models.CharField(max_length=100)),
                ('unit', models.ForeignKey(to='services.Unit', related_name='accessibility_properties')),
                ('variable', models.ForeignKey(to='services.AccessibilityVariable')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitConnection',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('type', models.IntegerField()),
                ('name', models.CharField(max_length=400)),
                ('name_fi', models.CharField(max_length=400, null=True)),
                ('name_sv', models.CharField(max_length=400, null=True)),
                ('name_en', models.CharField(max_length=400, null=True)),
                ('www_url', models.URLField(max_length=400, null=True)),
                ('www_url_fi', models.URLField(max_length=400, null=True)),
                ('www_url_sv', models.URLField(max_length=400, null=True)),
                ('www_url_en', models.URLField(max_length=400, null=True)),
                ('section', models.CharField(max_length=20)),
                ('contact_person', models.CharField(max_length=50, null=True)),
                ('email', models.EmailField(max_length=100, null=True)),
                ('phone', models.CharField(max_length=50, null=True)),
                ('phone_mobile', models.CharField(max_length=50, null=True)),
                ('unit', models.ForeignKey(to='services.Unit', related_name='connections')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='keyword',
            unique_together=set([('language', 'name')]),
        ),
        migrations.AddField(
            model_name='department',
            name='organization',
            field=models.ForeignKey(to='services.Organization'),
            preserve_default=True,
        ),
    ]
