from django.contrib.gis import admin

from exceptional_situations.models import (
    Situation,
    SituationAnnouncement,
    SituationLocation,
    SituationType,
)


class SituationAdmin(admin.ModelAdmin):
    list_display = ("is_active", "start_time", "end_time")


class SituationTypeAdmin(admin.ModelAdmin):
    list_display = ("type_name", "sub_type_name")


class SituationAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "start_time", "end_time")


class SituationLocationAdmin(admin.GISModelAdmin):
    list_display = ("id", "title", "geometry")

    def title(self, obj):
        return obj.announcement.title


admin.site.register(Situation, SituationAdmin)
admin.site.register(SituationType, SituationTypeAdmin)
admin.site.register(SituationAnnouncement, SituationAnnouncementAdmin)
admin.site.register(SituationLocation, SituationLocationAdmin)
