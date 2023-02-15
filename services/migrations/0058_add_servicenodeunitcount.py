# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-15 13:56
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("munigeo", "0004_building"),
        ("services", "0057_remove_service_unit_count"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServiceNodeUnitCount",
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
                ("count", models.PositiveIntegerField()),
                (
                    "division",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="munigeo.AdministrativeDivision",
                    ),
                ),
                (
                    "division_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="munigeo.AdministrativeDivisionType",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="servicenode",
            name="unit_count",
        ),
        migrations.AddField(
            model_name="servicenodeunitcount",
            name="service_node",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="services.ServiceNode"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="servicenodeunitcount",
            unique_together=set([("service_node", "division")]),
        ),
    ]
