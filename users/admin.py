from copy import deepcopy

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin


@admin.register(get_user_model())
class UserAdmin(DjangoUserAdmin):
    list_display = DjangoUserAdmin.list_display + ("is_superuser",)
    search_fields = DjangoUserAdmin.search_fields + ("id", "uuid")
    readonly_fields = ("id", "uuid")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            fieldsets = deepcopy(fieldsets)
            fieldsets[0][1]["fields"] += ("id", "uuid")
            fieldsets[2][1]["fields"] += ("department_name", "ad_groups")
        return fieldsets
