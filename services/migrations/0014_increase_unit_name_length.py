# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0013_increase_caption_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='name',
            field=models.CharField(max_length=210, db_index=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='name_en',
            field=models.CharField(max_length=210, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='name_fi',
            field=models.CharField(max_length=210, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='name_sv',
            field=models.CharField(max_length=210, null=True, db_index=True),
        ),
    ]
