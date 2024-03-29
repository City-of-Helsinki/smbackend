# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-27 15:37
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("services", "0030_reverse_unit_ordering"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="AllowedValue",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "identifier",
                    models.CharField(db_index=True, max_length=50, null=True),
                ),
                (
                    "quality",
                    models.CharField(
                        db_index=True, default="unknown", max_length=50, null=True
                    ),
                ),
                ("name", models.CharField(db_index=True, max_length=100, null=True)),
                ("name_fi", models.CharField(db_index=True, max_length=100, null=True)),
                ("name_sv", models.CharField(db_index=True, max_length=100, null=True)),
                ("name_en", models.CharField(db_index=True, max_length=100, null=True)),
                ("description", models.TextField()),
                ("description_fi", models.TextField(null=True)),
                ("description_sv", models.TextField(null=True)),
                ("description_en", models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name="ObservableProperty",
            fields=[
                (
                    "id",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(db_index=True, max_length=100)),
                ("measurement_unit", models.CharField(max_length=20, null=True)),
                ("observation_type", models.CharField(max_length=80)),
                (
                    "services",
                    models.ManyToManyField(
                        related_name="observable_properties", to="services.OntologyWord"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Observation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "time",
                    models.DateTimeField(
                        db_index=True, help_text="Exact time the observation was made"
                    ),
                ),
            ],
            options={
                "ordering": ["-time"],
            },
        ),
        migrations.CreateModel(
            name="PluralityAuthToken",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(db_index=True, max_length=40)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("active", models.BooleanField(default=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="auth_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UnitLatestObservation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserOrganization",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="services.Organization",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organization",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CategoricalObservation",
            fields=[
                (
                    "observation_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="observations.Observation",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("observations.observation",),
        ),
        migrations.CreateModel(
            name="DescriptiveObservation",
            fields=[
                (
                    "observation_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="observations.Observation",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("observations.observation",),
        ),
        migrations.AddField(
            model_name="unitlatestobservation",
            name="observation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="observations.Observation",
            ),
        ),
        migrations.AddField(
            model_name="unitlatestobservation",
            name="property",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="observations.ObservableProperty",
            ),
        ),
        migrations.AddField(
            model_name="unitlatestobservation",
            name="unit",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="latest_observations",
                to="services.Unit",
            ),
        ),
        migrations.AddField(
            model_name="observation",
            name="auth",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="observations.PluralityAuthToken",
            ),
        ),
        migrations.AddField(
            model_name="observation",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_observations.observation_set+",
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AddField(
            model_name="observation",
            name="property",
            field=models.ForeignKey(
                help_text="The property observed",
                on_delete=django.db.models.deletion.CASCADE,
                to="observations.ObservableProperty",
            ),
        ),
        migrations.AddField(
            model_name="observation",
            name="unit",
            field=models.ForeignKey(
                help_text="The unit the observation is about",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="observation_history",
                to="services.Unit",
            ),
        ),
        migrations.AddField(
            model_name="observation",
            name="units",
            field=models.ManyToManyField(
                through="observations.UnitLatestObservation", to="services.Unit"
            ),
        ),
        migrations.AddField(
            model_name="observation",
            name="value",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="instances",
                to="observations.AllowedValue",
            ),
        ),
        migrations.AddField(
            model_name="allowedvalue",
            name="property",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="allowed_values",
                to="observations.ObservableProperty",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="unitlatestobservation",
            unique_together=set([("unit", "property")]),
        ),
        migrations.AlterUniqueTogether(
            name="allowedvalue",
            unique_together=set([("identifier", "property")]),
        ),
    ]
