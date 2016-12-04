# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('observations', '0003_auto_20161203_2321'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='unitlatestobservation',
            unique_together=set([('unit', 'property')]),
        ),
    ]
