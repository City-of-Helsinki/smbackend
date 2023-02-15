# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0002_auto_20170403_1032"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="description_en",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="description_fi",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="description_sv",
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="name_en",
            field=models.CharField(max_length=200, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="name_fi",
            field=models.CharField(max_length=200, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="name_sv",
            field=models.CharField(max_length=200, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="picture_caption_en",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="picture_caption_fi",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="picture_caption_sv",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="street_address_en",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="street_address_fi",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="street_address_sv",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="www_en",
            field=models.URLField(max_length=400, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="www_fi",
            field=models.URLField(max_length=400, null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="www_sv",
            field=models.URLField(max_length=400, null=True),
        ),
    ]
