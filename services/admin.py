from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from services.models.notification import Announcement, ErrorMessage


class NotificationAdmin(TranslationAdmin):
    list_display = ("title", "active", "content")
    list_display_links = ("title", "content")
    list_filter = ("active",)


admin.site.register(Announcement, NotificationAdmin)
admin.site.register(ErrorMessage, NotificationAdmin)
