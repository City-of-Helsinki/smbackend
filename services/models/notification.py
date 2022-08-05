from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    title = models.CharField(blank=True, max_length=100, verbose_name=_("Title"))
    lead_paragraph = models.TextField(blank=True, verbose_name=_("Lead paragraph"))
    content = models.TextField(verbose_name=_("Content"))
    external_url = models.URLField(blank=True, verbose_name=_("External URL"))
    external_url_title = models.CharField(
        null=True, blank=True, max_length=100, verbose_name=_("External URL title")
    )
    picture_url = models.URLField(blank=True, verbose_name=_("Picture URL"))
    active = models.BooleanField(
        default=False,
        verbose_name=_("Active"),
        help_text=_("Only active objects are visible in the API."),
    )
    outdoor_sports_map_usage = models.BooleanField(
        default=False,
        verbose_name=_("Outdoor sports map usage"),
        help_text=_("Intented for outdoor sports map usage"),
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class Announcement(Notification):
    class Meta:
        ordering = ["-id"]
        verbose_name = _("announcement")
        verbose_name_plural = _("announcements")


class ErrorMessage(Notification):
    class Meta:
        ordering = ["-id"]
        verbose_name = _("error message")
        verbose_name_plural = _("error messages")
