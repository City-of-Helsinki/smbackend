# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0003_allowedvalue_quality'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='observation',
            options={'ordering': ['-time']},
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='description_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='description_fi',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='description_sv',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='name_en',
            field=models.CharField(null=True, max_length=100, db_index=True),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='name_fi',
            field=models.CharField(null=True, max_length=100, db_index=True),
        ),
        migrations.AddField(
            model_name='allowedvalue',
            name='name_sv',
            field=models.CharField(null=True, max_length=100, db_index=True),
        ),
    ]
