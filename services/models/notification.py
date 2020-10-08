from django.db import models


class Notification(models.Model):
    title = models.CharField(blank=True, max_length=100)
    content = models.TextField()
    active = models.BooleanField(
        default=False, help_text="Only active objects are visible in the API."
    )

    class Meta:
        abstract = True
        ordering = ["-id"]

    def __str__(self):
        return self.title


class Announcement(Notification):
    pass


class ErrorMessage(Notification):
    pass
