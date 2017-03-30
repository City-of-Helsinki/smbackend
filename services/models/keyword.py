from django.db import models
from django.conf import settings


class Keyword(models.Model):
    language = models.CharField(max_length=10, choices=settings.LANGUAGES, db_index=True)
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = (('language', 'name'),)

    def __str__(self):
        return "%s (%s)" % (self.name, self.language)
