# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-14 10:37
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0017_auto_20170512_0909"),
    ]

    operations = [
        migrations.RenameField(
            model_name="unit",
            old_name="root_servicenodes",
            new_name="root_ontologytreenodes",
        ),
    ]
