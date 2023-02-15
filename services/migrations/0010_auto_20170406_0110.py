# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0009_auto_20170403_1541"),
    ]

    operations = [
        migrations.AlterField(
            model_name="unit",
            name="provider_type",
            field=models.PositiveSmallIntegerField(
                null=True,
                choices=[
                    (1, "SELF_PRODUCED"),
                    (2, "MUNICIPALITY"),
                    (3, "ASSOCIATION"),
                    (4, "PRIVATE_COMPANY"),
                    (5, "OTHER_PRODUCTION_METHOD"),
                    (6, "PURCHASED_SERVICE"),
                    (7, "UNKNOWN_PRODUCTION_METHOD"),
                    (8, "CONTRACT_SCHOOL"),
                    (9, "SUPPORTED_OPERATIONS"),
                    (10, "PAYMENT_COMMITMENT"),
                ],
            ),
        ),
    ]
