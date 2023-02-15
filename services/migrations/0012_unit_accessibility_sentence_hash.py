# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0011_accessibilitysentence"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="accessibility_sentence_hash",
            field=models.CharField(max_length=40, null=True),
        ),
    ]
