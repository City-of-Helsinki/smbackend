# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.hstore
import mptt.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("munigeo", "0003_add_modified_time_to_address_and_street"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessibilityVariable",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("uuid", models.UUIDField(unique=True, db_index=True, editable=False)),
                ("business_id", models.CharField(max_length=10)),
                ("name", models.CharField(max_length=200, db_index=True)),
                ("name_fi", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_sv", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_en", models.CharField(max_length=200, null=True, db_index=True)),
                ("abbr", models.CharField(max_length=50, null=True, db_index=True)),
                ("abbr_fi", models.CharField(max_length=50, null=True, db_index=True)),
                ("abbr_sv", models.CharField(max_length=50, null=True, db_index=True)),
                ("abbr_en", models.CharField(max_length=50, null=True, db_index=True)),
                ("street_address", models.CharField(max_length=100, null=True)),
                ("street_address_fi", models.CharField(max_length=100, null=True)),
                ("street_address_sv", models.CharField(max_length=100, null=True)),
                ("street_address_en", models.CharField(max_length=100, null=True)),
                ("address_city", models.CharField(max_length=100, null=True)),
                ("address_city_fi", models.CharField(max_length=100, null=True)),
                ("address_city_sv", models.CharField(max_length=100, null=True)),
                ("address_city_en", models.CharField(max_length=100, null=True)),
                ("address_postal_full", models.CharField(max_length=200, null=True)),
                ("address_postal_full_fi", models.CharField(max_length=200, null=True)),
                ("address_postal_full_sv", models.CharField(max_length=200, null=True)),
                ("address_postal_full_en", models.CharField(max_length=200, null=True)),
                ("www", models.CharField(max_length=200, null=True)),
                ("www_fi", models.CharField(max_length=200, null=True)),
                ("www_sv", models.CharField(max_length=200, null=True)),
                ("www_en", models.CharField(max_length=200, null=True)),
                ("phone", models.CharField(max_length=30, null=True)),
                ("address_zip", models.CharField(max_length=10, null=True)),
                ("hierarchy_level", models.SmallIntegerField(null=True)),
                ("object_identifier", models.CharField(max_length=20, null=True)),
                ("organization_type", models.CharField(max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Keyword",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        max_length=10,
                        db_index=True,
                        choices=[
                            ("fi", "Finnish"),
                            ("sv", "Swedish"),
                            ("en", "English"),
                        ],
                    ),
                ),
                ("name", models.CharField(max_length=100, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("uuid", models.UUIDField(unique=True, db_index=True, editable=False)),
                ("business_id", models.CharField(max_length=10, null=True)),
                ("organization_type", models.CharField(max_length=40)),
                ("municipality_code", models.IntegerField(null=True, default=None)),
                ("data_source_url", models.URLField(blank=True, null=True)),
                ("name", models.CharField(max_length=200, blank=True, db_index=True)),
                (
                    "name_fi",
                    models.CharField(
                        max_length=200, blank=True, null=True, db_index=True
                    ),
                ),
                (
                    "name_sv",
                    models.CharField(
                        max_length=200, blank=True, null=True, db_index=True
                    ),
                ),
                (
                    "name_en",
                    models.CharField(
                        max_length=200, blank=True, null=True, db_index=True
                    ),
                ),
                (
                    "abbr",
                    models.CharField(
                        max_length=50, blank=True, null=True, db_index=True
                    ),
                ),
                (
                    "abbr_fi",
                    models.CharField(
                        max_length=50, blank=True, null=True, db_index=True
                    ),
                ),
                (
                    "abbr_sv",
                    models.CharField(
                        max_length=50, blank=True, null=True, db_index=True
                    ),
                ),
                (
                    "abbr_en",
                    models.CharField(
                        max_length=50, blank=True, null=True, db_index=True
                    ),
                ),
                (
                    "street_address",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "street_address_fi",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "street_address_sv",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "street_address_en",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "address_city",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "address_city_fi",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "address_city_sv",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "address_city_en",
                    models.CharField(max_length=100, blank=True, null=True),
                ),
                (
                    "address_postal_full",
                    models.CharField(max_length=200, blank=True, null=True),
                ),
                (
                    "address_postal_full_fi",
                    models.CharField(max_length=200, blank=True, null=True),
                ),
                (
                    "address_postal_full_sv",
                    models.CharField(max_length=200, blank=True, null=True),
                ),
                (
                    "address_postal_full_en",
                    models.CharField(max_length=200, blank=True, null=True),
                ),
                ("www", models.CharField(max_length=200, blank=True, null=True)),
                ("www_fi", models.CharField(max_length=200, blank=True, null=True)),
                ("www_sv", models.CharField(max_length=200, blank=True, null=True)),
                ("www_en", models.CharField(max_length=200, blank=True, null=True)),
                ("address_zip", models.CharField(max_length=10, blank=True, null=True)),
                ("phone", models.CharField(max_length=20, blank=True, null=True)),
                ("email", models.CharField(max_length=60, blank=True, null=True)),
                (
                    "object_identifier",
                    models.CharField(max_length=20, blank=True, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, db_index=True)),
                ("name_fi", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_sv", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_en", models.CharField(max_length=200, null=True, db_index=True)),
                ("unit_count", models.PositiveIntegerField(null=True)),
                (
                    "last_modified_time",
                    models.DateTimeField(
                        db_index=True, help_text="Time of last modification"
                    ),
                ),
                ("keywords", models.ManyToManyField(to="services.Keyword")),
            ],
        ),
        migrations.CreateModel(
            name="ServiceTreeNode",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200, db_index=True)),
                ("name_fi", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_sv", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_en", models.CharField(max_length=200, null=True, db_index=True)),
                ("unit_count", models.PositiveIntegerField(null=True)),
                ("ontologyword_reference", models.TextField(null=True)),
                (
                    "last_modified_time",
                    models.DateTimeField(
                        db_index=True, help_text="Time of last modification"
                    ),
                ),
                ("lft", models.PositiveIntegerField(db_index=True, editable=False)),
                ("rght", models.PositiveIntegerField(db_index=True, editable=False)),
                ("tree_id", models.PositiveIntegerField(db_index=True, editable=False)),
                ("level", models.PositiveIntegerField(db_index=True, editable=False)),
                ("keywords", models.ManyToManyField(to="services.Keyword")),
                (
                    "parent",
                    mptt.fields.TreeForeignKey(
                        null=True,
                        related_name="children",
                        to="services.ServiceTreeNode",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Unit",
            fields=[
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                ("data_source_url", models.URLField(null=True)),
                ("name", models.CharField(max_length=200, db_index=True)),
                ("name_fi", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_sv", models.CharField(max_length=200, null=True, db_index=True)),
                ("name_en", models.CharField(max_length=200, null=True, db_index=True)),
                ("description", models.TextField(null=True)),
                ("description_fi", models.TextField(null=True)),
                ("description_sv", models.TextField(null=True)),
                ("description_en", models.TextField(null=True)),
                ("provider_type", models.IntegerField()),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(
                        null=True, srid=3067
                    ),
                ),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.GeometryField(
                        null=True, srid=3067
                    ),
                ),
                ("street_address", models.CharField(max_length=100, null=True)),
                ("street_address_fi", models.CharField(max_length=100, null=True)),
                ("street_address_sv", models.CharField(max_length=100, null=True)),
                ("street_address_en", models.CharField(max_length=100, null=True)),
                ("address_zip", models.CharField(max_length=10, null=True)),
                ("phone", models.CharField(max_length=50, null=True)),
                ("email", models.EmailField(max_length=100, null=True)),
                ("www_url", models.URLField(max_length=400, null=True)),
                ("www_url_fi", models.URLField(max_length=400, null=True)),
                ("www_url_sv", models.URLField(max_length=400, null=True)),
                ("www_url_en", models.URLField(max_length=400, null=True)),
                ("address_postal_full", models.CharField(max_length=100, null=True)),
                ("data_source", models.CharField(max_length=20, null=True)),
                (
                    "extensions",
                    django.contrib.postgres.fields.hstore.HStoreField(null=True),
                ),
                ("picture_url", models.URLField(max_length=250, null=True)),
                ("picture_caption", models.CharField(max_length=200, null=True)),
                ("picture_caption_fi", models.CharField(max_length=200, null=True)),
                ("picture_caption_sv", models.CharField(max_length=200, null=True)),
                ("picture_caption_en", models.CharField(max_length=200, null=True)),
                (
                    "origin_last_modified_time",
                    models.DateTimeField(
                        db_index=True, help_text="Time of last modification"
                    ),
                ),
                (
                    "connection_hash",
                    models.CharField(
                        max_length=40,
                        null=True,
                        help_text="Automatically generated hash of connection info",
                    ),
                ),
                (
                    "accessibility_property_hash",
                    models.CharField(
                        max_length=40,
                        null=True,
                        help_text="Automatically generated hash of accessibility property info",
                    ),
                ),
                (
                    "identifier_hash",
                    models.CharField(
                        max_length=40,
                        null=True,
                        help_text="Automatically generated hash of other identifiers",
                    ),
                ),
                (
                    "root_services",
                    models.CommaSeparatedIntegerField(max_length=50, null=True),
                ),
                (
                    "root_servicenodes",
                    models.CommaSeparatedIntegerField(max_length=50, null=True),
                ),
                (
                    "department",
                    models.ForeignKey(
                        null=True, to="services.Department", on_delete=models.CASCADE
                    ),
                ),
                (
                    "divisions",
                    models.ManyToManyField(to="munigeo.AdministrativeDivision"),
                ),
                ("keywords", models.ManyToManyField(to="services.Keyword")),
                (
                    "municipality",
                    models.ForeignKey(
                        null=True, to="munigeo.Municipality", on_delete=models.CASCADE
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        to="services.Organization", on_delete=models.CASCADE
                    ),
                ),
                (
                    "service_tree_nodes",
                    models.ManyToManyField(
                        related_name="units", to="services.ServiceTreeNode"
                    ),
                ),
                (
                    "services",
                    models.ManyToManyField(related_name="units", to="services.Service"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UnitAccessibilityProperty",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("value", models.CharField(max_length=100)),
                (
                    "unit",
                    models.ForeignKey(
                        related_name="accessibility_properties",
                        to="services.Unit",
                        on_delete=models.CASCADE,
                    ),
                ),
                (
                    "variable",
                    models.ForeignKey(
                        to="services.AccessibilityVariable", on_delete=models.CASCADE
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UnitAlias",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("second", models.IntegerField(unique=True, db_index=True)),
                (
                    "first",
                    models.ForeignKey(
                        related_name="aliases",
                        to="services.Unit",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UnitConnection",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("type", models.IntegerField()),
                ("name", models.CharField(max_length=400)),
                ("name_fi", models.CharField(max_length=400, null=True)),
                ("name_sv", models.CharField(max_length=400, null=True)),
                ("name_en", models.CharField(max_length=400, null=True)),
                ("www_url", models.URLField(max_length=400, null=True)),
                ("www_url_fi", models.URLField(max_length=400, null=True)),
                ("www_url_sv", models.URLField(max_length=400, null=True)),
                ("www_url_en", models.URLField(max_length=400, null=True)),
                ("section", models.CharField(max_length=20)),
                ("contact_person", models.CharField(max_length=80, null=True)),
                ("email", models.EmailField(max_length=100, null=True)),
                ("phone", models.CharField(max_length=50, null=True)),
                ("phone_mobile", models.CharField(max_length=50, null=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                (
                    "unit",
                    models.ForeignKey(
                        related_name="connections",
                        to="services.Unit",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="UnitIdentifier",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("namespace", models.CharField(max_length=50)),
                ("value", models.CharField(max_length=100)),
                (
                    "unit",
                    models.ForeignKey(
                        related_name="identifiers",
                        to="services.Unit",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="keyword",
            unique_together=set([("language", "name")]),
        ),
        migrations.AddField(
            model_name="department",
            name="organization",
            field=models.ForeignKey(
                null=True, to="services.Organization", on_delete=models.CASCADE
            ),
        ),
    ]
