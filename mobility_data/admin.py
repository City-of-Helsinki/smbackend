from contextlib import suppress
from os import listdir, remove

from django.conf import settings
from django.contrib import admin, messages

from mobility_data.constants import DATA_SOURCE_IMPORTERS
from mobility_data.forms import CustomDataSourceForm
from mobility_data.models import (
    ContentType,
    DataSource,
    GroupType,
    MobileUnit,
    MobileUnitGroup,
)
from mobility_data.models.data_source import UPLOAD_TO

PATH = f"{settings.MEDIA_ROOT}/{UPLOAD_TO}/"


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance

    return Wrapper


class MobileUnitAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        # Show only MobileUnits that are stored into the MobileUnit table.
        # If MobileUnit has a unit_id, its data is serialized from
        # the Unit table, therefore it should not be shown/edited in the admin
        queryset = MobileUnit.objects.filter(unit_id__isnull=True)
        return queryset

    readonly_fields = ("id",)
    list_filter = (
        ("content_type__name", custom_titled_filter("Type Name")),
        "is_active",
        ("mobile_unit_group__name", custom_titled_filter("Group Name")),
    )
    list_display = (
        "unit_name",
        "type_name",
        "group_name",
    )
    search_fields = (
        "name",
        "name_sv",
        "name_en",
        "description",
        "description_sv",
        "description_en",
    )

    def unit_name(self, obj):
        # Return "Anonymous" as name for MobileUnits that do not have name
        if obj.name is None:
            return "Anonymous"
        else:
            return obj.name

    def type_name(self, obj):
        return obj.content_type.name

    def group_name(self, obj):
        if obj.mobile_unit_group is None:
            return ""
        else:
            return obj.mobile_unit_group.name


class MobileUnitGroupAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_filter = (("group_type__name", custom_titled_filter("Group Name")),)
    list_display = (
        "name",
        "type_name",
    )
    search_fields = (
        "name",
        "name_sv",
        "name_en",
        "description",
        "description_sv",
        "description_en",
    )

    def type_name(self, obj):
        return obj.group_type.name


class ContentTypeAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "type_name", "name", "description")


class GroupTypeAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "type_name", "name", "description")


class DataSourceAdmin(admin.ModelAdmin):
    form = CustomDataSourceForm
    list_display = (
        "name",
        "importer_name",
        "data_file",
    )

    def importer_name(self, obj):
        return DATA_SOURCE_IMPORTERS[obj.type_name]["importer_name"]

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            # Delete all files that are in the Deleted instances
            with suppress(OSError):
                remove(str(obj.data_file.file))
        super().delete_queryset(request, queryset)

    def error_message(self, request, message):
        # Set level to ERROR, otherwise a message will be displayed that informs of created instance
        messages.set_level(request, messages.ERROR)
        messages.error(request, message)

    def file_clean_up(self):
        """
        Delete files that are not connected to DataSource instance.
        """
        data_files = [
            str(data_source.data_file.file) for data_source in DataSource.objects.all()
        ]
        for file in listdir(PATH):
            file_name = PATH + file
            if file_name not in data_files:
                with suppress(OSError):
                    remove(file_name)

    def save_model(self, request, obj, form, change):
        data_source = None
        data_source_qs = DataSource.objects.filter(type_name=obj.type_name).exclude(
            id=obj.id
        )
        if data_source_qs.exists():
            self.error_message(request, "DataSource of given Type name exists.")
            return False

        if not obj.data_file:
            self.error_message(request, "No Data File given, data source not saved.")
            return False

        super().save_model(request, obj, form, change)
        self.file_clean_up()

        if "data_file" in form.changed_data:
            file_name = PATH + str(obj.data_file.file)
            # Check if file with same name exists.
            for data_source in DataSource.objects.all():
                if file_name == str(data_source.data_file.file):
                    self.error_message(
                        request,
                        "File with the same name exist with different Content Type, aborting.",
                    )
                    return False


admin.site.register(DataSource, DataSourceAdmin)
admin.site.register(MobileUnit, MobileUnitAdmin)
admin.site.register(MobileUnitGroup, MobileUnitGroupAdmin)
admin.site.register(ContentType, ContentTypeAdmin)
admin.site.register(GroupType, GroupTypeAdmin)
