# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0008_auto_20170403_1536"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="streetview_entrance_url",
            field=models.URLField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name="unit",
            name="picture_entrance_url",
            field=models.URLField(max_length=500, null=True),
        ),
    ]
