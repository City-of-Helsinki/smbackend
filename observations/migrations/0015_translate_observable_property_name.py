# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0014_rename_new_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='observableproperty',
            name='name_en',
            field=models.CharField(null=True, db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name='observableproperty',
            name='name_fi',
            field=models.CharField(null=True, db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name='observableproperty',
            name='name_sv',
            field=models.CharField(null=True, db_index=True, max_length=100),
        ),
    ]
