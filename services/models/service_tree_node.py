from django.db import models
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from services.utils import get_translated
from .keyword import Keyword
from .service import ServiceManager, ServiceQuerySet


class ServiceTreeNode(MPTTModel):
    id = models.IntegerField(primary_key=True)  # id of ontologytree
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')
    unit_count = models.PositiveIntegerField(null=True)
    keywords = models.ManyToManyField(Keyword)

    ontologyword_reference = models.TextField(null=True)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    objects = ServiceManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)
