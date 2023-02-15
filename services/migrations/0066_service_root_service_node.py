# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-02 08:27
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0065_longer_unit_phone_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="root_service_node",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="services.ServiceNode",
            ),
        ),
    ]
