# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(model_name="unit", name="description_en",),
        migrations.RemoveField(model_name="unit", name="description_fi",),
        migrations.RemoveField(model_name="unit", name="description_sv",),
        migrations.RemoveField(model_name="unit", name="extensions",),
        migrations.RemoveField(model_name="unit", name="name_en",),
        migrations.RemoveField(model_name="unit", name="name_fi",),
        migrations.RemoveField(model_name="unit", name="name_sv",),
        migrations.RemoveField(model_name="unit", name="origin_last_modified_time",),
        migrations.RemoveField(model_name="unit", name="picture_caption_en",),
        migrations.RemoveField(model_name="unit", name="picture_caption_fi",),
        migrations.RemoveField(model_name="unit", name="picture_caption_sv",),
        migrations.RemoveField(model_name="unit", name="street_address_en",),
        migrations.RemoveField(model_name="unit", name="street_address_fi",),
        migrations.RemoveField(model_name="unit", name="street_address_sv",),
        migrations.RemoveField(model_name="unit", name="www_url",),
        migrations.RemoveField(model_name="unit", name="www_url_en",),
        migrations.RemoveField(model_name="unit", name="www_url_fi",),
        migrations.RemoveField(model_name="unit", name="www_url_sv",),
        migrations.AddField(
            model_name="unit",
            name="accessibility_email",
            field=models.EmailField(null=True, max_length=100),
        ),
        migrations.AddField(
            model_name="unit",
            name="accessibility_phone",
            field=models.CharField(null=True, max_length=50),
        ),
        migrations.AddField(
            model_name="unit",
            name="accessibility_www",
            field=models.URLField(null=True, max_length=400),
        ),
        migrations.AddField(
            model_name="unit",
            name="address_city",
            field=models.CharField(null=True, max_length=100),
        ),
        migrations.AddField(
            model_name="unit",
            name="call_charge_info",
            field=models.CharField(null=True, max_length=100),
        ),
        migrations.AddField(
            model_name="unit",
            name="created_time",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="unit", name="desc", field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="extra_searchwords",
            field=models.CharField(null=True, max_length=200),
        ),
        migrations.AddField(
            model_name="unit",
            name="fax",
            field=models.CharField(null=True, max_length=50),
        ),
        migrations.AddField(
            model_name="unit",
            name="modified_time",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="organizer_business_id",
            field=models.CharField(null=True, max_length=10),
        ),
        migrations.AddField(
            model_name="unit",
            name="organizer_name",
            field=models.CharField(null=True, max_length=100),
        ),
        migrations.AddField(
            model_name="unit",
            name="organizer_type",
            field=models.CharField(null=True, max_length=50),
        ),
        migrations.AddField(
            model_name="unit",
            name="picture_entrance_url",
            field=models.URLField(null=True, max_length=250),
        ),
        migrations.AddField(
            model_name="unit", name="short_desc", field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name="unit",
            name="www",
            field=models.URLField(null=True, max_length=400),
        ),
    ]
