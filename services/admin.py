from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from services.models import (
    Announcement,
    ErrorMessage,
    FeedbackMapping,
    RequestStatistic,
)


class NotificationAdmin(TranslationAdmin):
    list_display = ("title", "active", "content")
    list_display_links = ("title", "content")
    list_filter = ("active",)


class FeedbackMappingAdmin(admin.ModelAdmin):
    list_display = (
        "abbr_fi",
        "service_code",
        "name_fi",
        "name_sv",
        "name_en",
        "department",
        "organization",
    )


class RequestStatisticAdmin(admin.ModelAdmin):
    list_display = ("timeframe", "request_counter", "details")


admin.site.register(Announcement, NotificationAdmin)
admin.site.register(ErrorMessage, NotificationAdmin)
admin.site.register(FeedbackMapping, FeedbackMappingAdmin)
admin.site.register(RequestStatistic, RequestStatisticAdmin)
