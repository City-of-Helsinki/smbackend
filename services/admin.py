from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from services.models.notification import Announcement, ErrorMessage
from services.models.statistic import RequestStatistic


class NotificationAdmin(TranslationAdmin):
    list_display = ("title", "active", "content")
    list_display_links = ("title", "content")
    list_filter = ("active",)


class RequestStatisticAdmin(admin.ModelAdmin):
    list_display = ("timeframe", "request_counter", "details")


admin.site.register(Announcement, NotificationAdmin)
admin.site.register(ErrorMessage, NotificationAdmin)
admin.site.register(RequestStatistic, RequestStatisticAdmin)
