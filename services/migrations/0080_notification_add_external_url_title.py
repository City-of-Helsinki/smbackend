# Generated by Django 2.2.13 on 2020-10-16 11:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0079_update_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcement",
            name="external_url_title",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
        migrations.AddField(
            model_name="announcement",
            name="external_url_title_en",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
        migrations.AddField(
            model_name="announcement",
            name="external_url_title_fi",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
        migrations.AddField(
            model_name="announcement",
            name="external_url_title_sv",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url_title",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url_title_en",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url_title_fi",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url_title_sv",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="External URL title"
            ),
        ),
    ]
