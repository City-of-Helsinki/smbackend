from django.contrib import admin

from mobility_data.models import (
    MobileUnit,
    MobileUnitGroup,
    ContentType,
    GroupType
)
def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


class MobileUnitAdmin(admin.ModelAdmin):
    readonly_fields=("id",)
    list_filter=(
        ("content_type__name",custom_titled_filter("Type Name")),       
        "is_active",
        ("mobile_unit_group__name",custom_titled_filter("Group Name")),
    )
    list_display=(
        "unit_name",
        "type_name",
        "group_name",
    )
    search_fields = ("name", "name_sv", "name_en", 
        "description", "description_sv", "description_en",)
    
    def unit_name(self, obj):
        #Return "Anonymous" as name for MobileUnits that do not have name
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
    readonly_fields=("id",)
    list_filter=(
        ("group_type__name",custom_titled_filter("Group Name")),      
       
    )
    list_display=(
        "name",
        "type_name",        
    )
    search_fields = ("name", "name_sv", "name_en",     
        "description", "description_sv", "description_en",)

    def type_name(self, obj):
        return obj.group_type.name


class ContentTypeAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "type_name", "name", "description")
    

class GroupTypeAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "type_name", "name", "description")


admin.site.register(MobileUnit, MobileUnitAdmin)
admin.site.register(MobileUnitGroup, MobileUnitGroupAdmin)
admin.site.register(ContentType, ContentTypeAdmin)
admin.site.register(GroupType, GroupTypeAdmin)