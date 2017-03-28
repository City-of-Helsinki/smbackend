# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0015_auto_20170324_1427'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicetreenode',
            name='ontologyword_reference',
            field=models.TextField(null=True),
        ),
    ]
