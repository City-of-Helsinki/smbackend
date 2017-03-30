from django.db import models
from services.utils import get_translated


class Organization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    data_source_url = models.URLField(max_length=200)

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)
