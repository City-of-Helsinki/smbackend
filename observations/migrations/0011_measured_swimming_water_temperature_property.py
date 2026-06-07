from django.db import migrations

PROPERTY_ID = "measured_swimming_water_temperature"
SERVICE_IDS = [730, 731]


def create_property(apps, schema_editor):
    observable_property_model = apps.get_model("observations", "ObservableProperty")
    service_model = apps.get_model("services", "Service")

    prop, _ = observable_property_model.objects.update_or_create(
        id=PROPERTY_ID,
        defaults={
            "name": "Water temperature (measured)",
            "name_fi": "Veden lämpötila (mitattu)",
            "name_sv": "Vattentemperatur (uppmätt)",
            "name_en": "Water temperature (measured)",
            "measurement_unit": "°C",
            "observation_type": "observations.MeasuredObservation",
        },
    )

    existing_services = service_model.objects.filter(id__in=SERVICE_IDS)
    if existing_services.exists():
        prop.services.add(*existing_services)


def remove_property(apps, schema_editor):
    observable_property_model = apps.get_model("observations", "ObservableProperty")
    observable_property_model.objects.filter(id=PROPERTY_ID).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("observations", "0010_add_measured_observation"),
        ("services", "0121_make_requeststatistic_timeframe_unique"),
    ]

    operations = [
        migrations.RunPython(create_property, remove_property),
    ]
