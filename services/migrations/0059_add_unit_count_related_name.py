# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-17 11:34
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0058_add_servicenodeunitcount"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servicenodeunitcount",
            name="service_node",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="unit_counts",
                to="services.ServiceNode",
            ),
        ),
    ]
