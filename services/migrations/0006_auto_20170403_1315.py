# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0005_auto_20170403_1131"),
    ]

    operations = [
        migrations.RemoveField(model_name="unitconnection", name="contact_person",),
        migrations.RemoveField(model_name="unitconnection", name="phone",),
        migrations.RemoveField(model_name="unitconnection", name="phone_mobile",),
        migrations.RemoveField(model_name="unitconnection", name="section",),
        migrations.RemoveField(model_name="unitconnection", name="type",),
        migrations.AddField(
            model_name="unitconnection",
            name="section_type",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "PHONE_OR_EMAIL"), (2, "LINK")], null=True
            ),
        ),
        migrations.AlterField(
            model_name="unit",
            name="provider_type",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "SELF_PRODUCED"),
                    (2, "MUNICIPALITY"),
                    (3, "ASSOCIATION"),
                    (4, "PRIVATE_COMPANY"),
                ]
            ),
        ),
    ]
