from django.db import models
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from services.utils import get_translated


# ex. ServiceType
class Service(models.Model):
    id = models.IntegerField(primary_key=True) # id of ontologyword
    name = models.CharField(max_length=200, db_index=True)

    unit_count = models.PositiveIntegerField(null=True)
    keywords = models.ManyToManyField(Keyword)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)


