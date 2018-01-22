# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0012_unit_data_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='picture_caption',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_caption_en',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_caption_fi',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_caption_sv',
            field=models.CharField(max_length=250, null=True),
        ),
    ]
