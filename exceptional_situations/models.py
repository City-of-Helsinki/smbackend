from datetime import datetime

from django.contrib.gis.db import models
from django.utils import timezone
from munigeo.models import Municipality

PROJECTION_SRID = 4326


class SituationType(models.Model):
    type_name = models.CharField(max_length=64)
    sub_type_name = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return "%s (%s)" % (self.type_name, self.id)


class SituationLocation(models.Model):
    location = models.PointField(null=True, blank=True, srid=PROJECTION_SRID)
    geometry = models.GeometryField(null=True, blank=True, srid=PROJECTION_SRID)
    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["id"]


class SituationAnnouncement(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    additional_info = models.JSONField(null=True, blank=True)
    location = models.ForeignKey(
        SituationLocation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="announcements",
    )
    municipalities = models.ManyToManyField(Municipality)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return "%s (%s)" % (self.title, self.id)


class Situation(models.Model):
    situation_id = models.CharField(max_length=64)
    situation_type = models.ForeignKey(SituationType, on_delete=models.CASCADE)
    release_time = models.DateTimeField(null=True, blank=True)
    announcements = models.ManyToManyField(SituationAnnouncement)

    class Meta:
        ordering = ["id"]

    @property
    def situation_type_str(self) -> str:
        return self.situation_type.type_name

    @property
    def situation_sub_type_str(self) -> str:
        return self.situation_type.sub_type_name

    @property
    def is_active(self) -> bool:
        if not self.announcements.exists():
            return False

        start_times_in_future = all(
            {a.start_time > timezone.now() for a in self.announcements.all()}
        )
        # If all start times are in future, return False
        if start_times_in_future:
            return False
        # If one or more end_time is null(unknown?) the situation is active
        if self.announcements.filter(end_time__isnull=True).exists():
            return True

        # If end_time is past for all announcements, return True, else False
        return any(
            {
                a.end_time > timezone.now()
                for a in self.announcements.filter(end_time__isnull=False)
            }
        )

    @property
    def start_time(self) -> datetime:
        """
        Return the start_time that is furthest in history
        """
        start_time = None
        for announcement in self.announcements.all():
            if not start_time:
                start_time = announcement.start_time
            if announcement.start_time < start_time:
                start_time = announcement.start_time
        return start_time

    @property
    def end_time(self) -> datetime:
        """
        Return the end_time that is furthest in future
        """
        end_time = None
        for announcement in self.announcements.filter(end_time__isnull=False):
            if not end_time:
                end_time = announcement.end_time

            if announcement.end_time > end_time:
                end_time = announcement.end_time
        return end_time
