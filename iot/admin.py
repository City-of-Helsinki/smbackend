from django.contrib import admin
from iot.models import IoTDataSource
from iot.utils import clear_source_names_from_cache


class IoTDataSourceAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # clear the cache of source_names
        clear_source_names_from_cache()
        return super().save_model(request, obj, form, change)

    # def delete_queryset(self, request, queryset):
    #     # Delete all IoTData for the source.
    #     for q in queryset:
    #         IoTData.objects.filter(source_name=q.source_name).delete()
    #     return super().delete_queryset(request, queryset)


admin.site.register(IoTDataSource, IoTDataSourceAdmin)
