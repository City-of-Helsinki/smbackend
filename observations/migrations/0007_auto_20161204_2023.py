# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0006_pluralityauthtoken_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='observation',
            options={},
        ),
        migrations.AddField(
            model_name='observation',
            name='auth',
            field=models.ForeignKey(default=1, to='observations.PluralityAuthToken'),
            preserve_default=False,
        ),
    ]
