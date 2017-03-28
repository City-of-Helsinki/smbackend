# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0014_auto_20170323_1354'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceTreeNode',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('name_fi', models.CharField(null=True, max_length=200, db_index=True)),
                ('name_sv', models.CharField(null=True, max_length=200, db_index=True)),
                ('name_en', models.CharField(null=True, max_length=200, db_index=True)),
                ('unit_count', models.PositiveIntegerField(null=True)),
                ('last_modified_time', models.DateTimeField(help_text='Time of last modification', db_index=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('keywords', models.ManyToManyField(to='services.Keyword')),
                ('parent', mptt.fields.TreeForeignKey(to='services.ServiceTreeNode', null=True, related_name='children')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RenameModel(
            old_name='ServiceLeaf',
            new_name='ServiceType',
        ),
        migrations.RemoveField(
            model_name='servicenode',
            name='keywords',
        ),
        migrations.RemoveField(
            model_name='servicenode',
            name='leaves',
        ),
        migrations.RemoveField(
            model_name='servicenode',
            name='parent',
        ),
        migrations.DeleteModel(
            name='ServiceNode',
        ),
    ]
