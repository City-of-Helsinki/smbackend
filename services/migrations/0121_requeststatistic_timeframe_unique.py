from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0120_set_manual_maintenance_organization"),
    ]

    operations = [
        migrations.AlterField(
            model_name="requeststatistic",
            name="timeframe",
            field=models.CharField(max_length=10, unique=True, verbose_name="Timeframe"),
        ),
    ]