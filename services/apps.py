from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.models import signals


class ServicesConfig(AppConfig):
    name = "services"
    verbose_name = _("Services")

    def ready(self): 
        # register signals       
        from services import signals

    
