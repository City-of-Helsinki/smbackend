# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-04 15:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0056_unit_accessibility_viewpoint_nullable"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="service",
            name="unit_count",
        ),
    ]
