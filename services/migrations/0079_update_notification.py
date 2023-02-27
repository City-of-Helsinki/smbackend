# Generated by Django 2.2.13 on 2020-10-13 15:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0078_announcement_errormessage"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="announcement",
            options={
                "ordering": ["-id"],
                "verbose_name": "announcement",
                "verbose_name_plural": "announcements",
            },
        ),
        migrations.AlterModelOptions(
            name="errormessage",
            options={
                "ordering": ["-id"],
                "verbose_name": "error message",
                "verbose_name_plural": "error messages",
            },
        ),
        migrations.AlterModelOptions(
            name="servicenode",
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="announcement",
            name="external_url",
            field=models.URLField(blank=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="announcement",
            name="external_url_en",
            field=models.URLField(blank=True, null=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="announcement",
            name="external_url_fi",
            field=models.URLField(blank=True, null=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="announcement",
            name="external_url_sv",
            field=models.URLField(blank=True, null=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="announcement",
            name="lead_paragraph",
            field=models.TextField(blank=True, verbose_name="Lead paragraph"),
        ),
        migrations.AddField(
            model_name="announcement",
            name="lead_paragraph_en",
            field=models.TextField(
                blank=True, null=True, verbose_name="Lead paragraph"
            ),
        ),
        migrations.AddField(
            model_name="announcement",
            name="lead_paragraph_fi",
            field=models.TextField(
                blank=True, null=True, verbose_name="Lead paragraph"
            ),
        ),
        migrations.AddField(
            model_name="announcement",
            name="lead_paragraph_sv",
            field=models.TextField(
                blank=True, null=True, verbose_name="Lead paragraph"
            ),
        ),
        migrations.AddField(
            model_name="announcement",
            name="picture_url",
            field=models.URLField(blank=True, verbose_name="Picture URL"),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url",
            field=models.URLField(blank=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url_en",
            field=models.URLField(blank=True, null=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url_fi",
            field=models.URLField(blank=True, null=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="external_url_sv",
            field=models.URLField(blank=True, null=True, verbose_name="External URL"),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="lead_paragraph",
            field=models.TextField(blank=True, verbose_name="Lead paragraph"),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="lead_paragraph_en",
            field=models.TextField(
                blank=True, null=True, verbose_name="Lead paragraph"
            ),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="lead_paragraph_fi",
            field=models.TextField(
                blank=True, null=True, verbose_name="Lead paragraph"
            ),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="lead_paragraph_sv",
            field=models.TextField(
                blank=True, null=True, verbose_name="Lead paragraph"
            ),
        ),
        migrations.AddField(
            model_name="errormessage",
            name="picture_url",
            field=models.URLField(blank=True, verbose_name="Picture URL"),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="active",
            field=models.BooleanField(
                default=False,
                help_text="Only active objects are visible in the API.",
                verbose_name="Active",
            ),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="content",
            field=models.TextField(verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="content_en",
            field=models.TextField(null=True, verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="content_fi",
            field=models.TextField(null=True, verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="content_sv",
            field=models.TextField(null=True, verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="title",
            field=models.CharField(blank=True, max_length=100, verbose_name="Title"),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="title_en",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Title"
            ),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="title_fi",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Title"
            ),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="title_sv",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Title"
            ),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="active",
            field=models.BooleanField(
                default=False,
                help_text="Only active objects are visible in the API.",
                verbose_name="Active",
            ),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="content",
            field=models.TextField(verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="content_en",
            field=models.TextField(null=True, verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="content_fi",
            field=models.TextField(null=True, verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="content_sv",
            field=models.TextField(null=True, verbose_name="Content"),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="title",
            field=models.CharField(blank=True, max_length=100, verbose_name="Title"),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="title_en",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Title"
            ),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="title_fi",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Title"
            ),
        ),
        migrations.AlterField(
            model_name="errormessage",
            name="title_sv",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Title"
            ),
        ),
    ]
