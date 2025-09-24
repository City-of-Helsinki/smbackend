from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from services.models import (
    Announcement,
    ErrorMessage,
    FeedbackMapping,
    RequestStatistic,
)


@admin.register(Announcement, ErrorMessage)
class NotificationAdmin(TranslationAdmin):
    list_display = ("title", "active", "content")
    list_display_links = ("title", "content")
    list_filter = ("active",)


@admin.register(FeedbackMapping)
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


@admin.register(RequestStatistic)
class RequestStatisticAdmin(admin.ModelAdmin):
    list_display = ("timeframe", "request_counter", "details")
