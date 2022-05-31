from django.apps import AppConfig


class MobilityDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mobility_data"

    def ready(self):
        # register signals
        from mobility_data import signals  # noqa: F401
