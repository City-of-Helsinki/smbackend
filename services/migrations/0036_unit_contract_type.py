# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-29 07:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0035_merge_20170816_1916"),
    ]

    operations = [
        migrations.AddField(
            model_name="unit",
            name="contract_type",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "contract_school"),
                    (1, "municipal_service"),
                    (2, "private_service"),
                    (3, "purchased_service"),
                    (4, "service_by_joint_municipal_authority"),
                    (5, "service_by_municipal_group_entity"),
                    (6, "service_by_municipally_owned_company"),
                    (7, "service_by_other_municipality"),
                    (8, "service_by_regional_cooperation_organization"),
                    (9, "state_service"),
                    (10, "supported_operations"),
                    (11, "voucher_service"),
                ],
                null=True,
            ),
        ),
    ]
