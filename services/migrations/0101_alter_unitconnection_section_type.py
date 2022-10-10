# Generated by Django 4.1.1 on 2022-09-30 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0100_add_service_keyword_names"),
    ]

    operations = [
        migrations.AlterField(
            model_name="unitconnection",
            name="section_type",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "PHONE_OR_EMAIL"),
                    (2, "LINK"),
                    (3, "TOPICAL"),
                    (4, "OTHER_INFO"),
                    (5, "OPENING_HOURS"),
                    (6, "SOCIAL_MEDIA_LINK"),
                    (7, "OTHER_ADDRESS"),
                    (8, "HIGHLIGHT"),
                    (9, "ESERVICE_LINK"),
                    (10, "PRICE"),
                    (11, "SUBGROUP"),
                    (12, "OPENING_HOUR_OBJECT"),
                ],
                null=True,
            ),
        ),
    ]