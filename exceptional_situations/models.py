from django.contrib.gis.db import models
from django.utils import timezone

PROJECTION_SRID = 4326


class SituationType(models.Model):
    type_name = models.CharField(max_length=64)
    sub_type_name = models.CharField(max_length=64, null=True, blank=True)


class SituationLocation(models.Model):
    location = models.PointField(null=True, blank=True, srid=PROJECTION_SRID)
    geometry = models.GeometryField(null=True, blank=True, srid=PROJECTION_SRID)
    details = models.JSONField(null=True, blank=True)


class SituationAnnouncement(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    additional_info = models.JSONField(null=True, blank=True)
    location = models.OneToOneField(SituationLocation, on_delete=models.CASCADE)


class Situation(models.Model):
    situation_id = models.CharField(max_length=64)
    situation_type = models.ForeignKey(SituationType, on_delete=models.CASCADE)
    release_time = models.DateTimeField()
    locations = models.ManyToManyField(SituationLocation)
    announcements = models.ManyToManyField(SituationAnnouncement)

    @property
    def situation_type_str(self):
        return self.situation_type.type_name

    @property
    def situation_sub_type_str(self):
        return self.situation_type.sub_type_name

    @property
    def is_active(self):
        # If one or more end_time is null(unknown?) the situation is active
        if self.announcements.filter(end_time__isnull=True).exists():
            return True

        # If end_time is past for all announcements, retrun True, else False
        return all(
            {
                not a.end_time < timezone.now()
                for a in self.announcements.filter(end_time__isnull=False)
            }
        )

    @property
    def situation_start_time(self):
        """
        Return start_time furthest in history
        """
        start_time = None
        for announcement in self.announcements.all():
            if not start_time:
                start_time = announcement.start_time
            if start_time < announcement.start_time:
                start_time = announcement.start_time
        return start_time

    @property
    def situation_end_time(self):
        """
        Return end_time furthest in future
        """
        end_time = None
        for announcement in self.announcements.filter(end_time__isnull=False):
            if not end_time:
                end_time = announcement.end_time

            if end_time > announcement.end_time:
                end_time = announcement.end_time
        return end_time
