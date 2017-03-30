# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields
import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('munigeo', '0003_add_modified_time_to_address_and_street'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessibilityVariable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.UUIDField(serialize=False, primary_key=True)),
                ('business_id', models.CharField(max_length=10)),
                ('hierarchy_level', models.SmallIntegerField()),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_sv', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_en', models.CharField(db_index=True, null=True, max_length=200)),
                ('object_identifier', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('language', models.CharField(db_index=True, choices=[('fi', 'Finnish'), ('sv', 'Swedish'), ('en', 'English')], max_length=10)),
                ('name', models.CharField(db_index=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_sv', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_en', models.CharField(db_index=True, null=True, max_length=200)),
                ('data_source_url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_sv', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_en', models.CharField(db_index=True, null=True, max_length=200)),
                ('unit_count', models.PositiveIntegerField(null=True)),
                ('last_modified_time', models.DateTimeField(db_index=True, help_text='Time of last modification')),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceTreeNode',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_sv', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_en', models.CharField(db_index=True, null=True, max_length=200)),
                ('unit_count', models.PositiveIntegerField(null=True)),
                ('ontologyword_reference', models.TextField(null=True)),
                ('last_modified_time', models.DateTimeField(db_index=True, help_text='Time of last modification')),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
                ('parent', mptt.fields.TreeForeignKey(null=True, to='services.ServiceTreeNode', related_name='children')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('data_source_url', models.URLField(null=True)),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('name_fi', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_sv', models.CharField(db_index=True, null=True, max_length=200)),
                ('name_en', models.CharField(db_index=True, null=True, max_length=200)),
                ('description', models.TextField(null=True)),
                ('description_fi', models.TextField(null=True)),
                ('description_sv', models.TextField(null=True)),
                ('description_en', models.TextField(null=True)),
                ('provider_type', models.IntegerField()),
                ('location', django.contrib.gis.db.models.fields.PointField(null=True, srid=3067)),
                ('geometry', django.contrib.gis.db.models.fields.GeometryField(null=True, srid=3067)),
                ('street_address', models.CharField(null=True, max_length=100)),
                ('street_address_fi', models.CharField(null=True, max_length=100)),
                ('street_address_sv', models.CharField(null=True, max_length=100)),
                ('street_address_en', models.CharField(null=True, max_length=100)),
                ('address_zip', models.CharField(null=True, max_length=10)),
                ('phone', models.CharField(null=True, max_length=50)),
                ('email', models.EmailField(null=True, max_length=100)),
                ('www_url', models.URLField(null=True, max_length=400)),
                ('www_url_fi', models.URLField(null=True, max_length=400)),
                ('www_url_sv', models.URLField(null=True, max_length=400)),
                ('www_url_en', models.URLField(null=True, max_length=400)),
                ('address_postal_full', models.CharField(null=True, max_length=100)),
                ('data_source', models.CharField(null=True, max_length=20)),
                ('extensions', django.contrib.postgres.fields.hstore.HStoreField(null=True)),
                ('picture_url', models.URLField(null=True, max_length=250)),
                ('picture_caption', models.CharField(null=True, max_length=200)),
                ('picture_caption_fi', models.CharField(null=True, max_length=200)),
                ('picture_caption_sv', models.CharField(null=True, max_length=200)),
                ('picture_caption_en', models.CharField(null=True, max_length=200)),
                ('origin_last_modified_time', models.DateTimeField(db_index=True, help_text='Time of last modification')),
                ('connection_hash', models.CharField(help_text='Automatically generated hash of connection info', null=True, max_length=40)),
                ('accessibility_property_hash', models.CharField(help_text='Automatically generated hash of accessibility property info', null=True, max_length=40)),
                ('identifier_hash', models.CharField(help_text='Automatically generated hash of other identifiers', null=True, max_length=40)),
                ('root_services', models.CommaSeparatedIntegerField(null=True, max_length=50)),
                ('root_servicenodes', models.CommaSeparatedIntegerField(null=True, max_length=50)),
                ('department', models.ForeignKey(null=True, to='services.Department')),
                ('divisions', models.ManyToManyField(to='munigeo.AdministrativeDivision')),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
                ('municipality', models.ForeignKey(null=True, to='munigeo.Municipality')),
                ('organization', models.ForeignKey(to='services.Organization')),
                ('service_tree_nodes', models.ManyToManyField(to='services.ServiceTreeNode', related_name='units')),
                ('services', models.ManyToManyField(to='services.Service', related_name='units')),
            ],
        ),
        migrations.CreateModel(
            name='UnitAccessibilityProperty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('value', models.CharField(max_length=100)),
                ('unit', models.ForeignKey(to='services.Unit', related_name='accessibility_properties')),
                ('variable', models.ForeignKey(to='services.AccessibilityVariable')),
            ],
        ),
        migrations.CreateModel(
            name='UnitConnection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('type', models.IntegerField()),
                ('name', models.CharField(max_length=400)),
                ('name_fi', models.CharField(null=True, max_length=400)),
                ('name_sv', models.CharField(null=True, max_length=400)),
                ('name_en', models.CharField(null=True, max_length=400)),
                ('www_url', models.URLField(null=True, max_length=400)),
                ('www_url_fi', models.URLField(null=True, max_length=400)),
                ('www_url_sv', models.URLField(null=True, max_length=400)),
                ('www_url_en', models.URLField(null=True, max_length=400)),
                ('section', models.CharField(max_length=20)),
                ('contact_person', models.CharField(null=True, max_length=80)),
                ('email', models.EmailField(null=True, max_length=100)),
                ('phone', models.CharField(null=True, max_length=50)),
                ('phone_mobile', models.CharField(null=True, max_length=50)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('unit', models.ForeignKey(to='services.Unit', related_name='connections')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='UnitIdentifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('namespace', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=100)),
                ('unit', models.ForeignKey(to='services.Unit', related_name='identifiers')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='keyword',
            unique_together=set([('language', 'name')]),
        ),
    ]
