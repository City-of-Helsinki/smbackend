# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0003_auto_20170403_1036"),
    ]

    operations = [
        migrations.AlterField(
            model_name="unit",
            name="provider_type",
            field=models.SmallIntegerField(
                choices=[
                    (1, "SELF_PRODUCED"),
                    (2, "MUNICIPALITY"),
                    (3, "ASSOCIATION"),
                    (4, "PRIVATE_COMPANY"),
                ]
            ),
        ),
    ]
