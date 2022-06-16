from django.contrib import admin

from iot.models import IoTDataSource
from iot.utils import clear_source_names_from_cache


class IoTDataSourceAdmin(admin.ModelAdmin):
    list_display = (("source_full_name"),)

    def save_model(self, request, obj, form, change):
        # clear the cache of source_names
        clear_source_names_from_cache()
        return super().save_model(request, obj, form, change)


admin.site.register(IoTDataSource, IoTDataSourceAdmin)
