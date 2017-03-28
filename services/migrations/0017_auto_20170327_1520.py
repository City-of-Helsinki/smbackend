# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0016_servicetreenode_ontologyword_reference'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='root_servicenodes',
            field=models.CommaSeparatedIntegerField(null=True, max_length=50),
        ),
        migrations.AddField(
            model_name='unit',
            name='service_tree_nodes',
            field=models.ManyToManyField(related_name='units', to='services.ServiceTreeNode'),
        ),
        migrations.AddField(
            model_name='unit',
            name='service_types',
            field=models.ManyToManyField(related_name='units', to='services.ServiceType'),
        ),
    ]
