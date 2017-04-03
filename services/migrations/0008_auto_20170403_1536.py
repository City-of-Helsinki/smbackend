# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0007_auto_20170403_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='extra_searchwords',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_caption',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_caption_en',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_caption_fi',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='picture_caption_sv',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='unit',
            name='provider_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'SELF_PRODUCED'), (2, 'MUNICIPALITY'), (3, 'ASSOCIATION'), (4, 'PRIVATE_COMPANY'), (5, 'OTHER_PRODUCTION_METHOD'), (6, 'PURCHASED_SERVICE'), (7, 'UNKNOWN_PRODUCTION_METHOD'), (8, 'CONTRACT_SCHOOL'), (9, 'SUPPORTED_OPERATIONS')]),
        ),
        migrations.AlterField(
            model_name='unitconnection',
            name='section_type',
            field=models.PositiveSmallIntegerField(null=True, choices=[(1, 'PHONE_OR_EMAIL'), (2, 'LINK'), (3, 'TOPICAL'), (4, 'OTHER_INFO'), (5, 'OPENING_HOURS'), (6, 'SOCIAL_MEDIA_LINK'), (7, 'OTHER_ADDRESS')]),
        ),
    ]
