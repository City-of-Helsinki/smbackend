from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from services.utils import get_translated
from .keyword import Keyword
from .unit import Unit
from .hierarchy import CustomTreeManager
from .ontology_word import OntologyWord


class ServiceNode(MPTTModel):
    id = models.IntegerField(primary_key=True)  # id of ontologytree
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')
    unit_count = models.PositiveIntegerField(null=True)
    keywords = models.ManyToManyField(Keyword)

    ontologyword_reference = models.TextField(null=True)
    related_ontologywords = models.ManyToManyField(OntologyWord)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    objects = CustomTreeManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

    def get_unit_count(self):
        srv_list = set(ServiceNode.objects.all().by_ancestor(self).values_list('id', flat=True))
        srv_list.add(self.id)
        count = Unit.objects.filter(public=True, service_nodes__in=list(srv_list)).distinct().count()
        return count

    def period_enabled(self):
        """Iterates through related ontologywords to find out
        if the tree node has periods enabled via ontologywords"""
        return next((
            o.period_enabled
            for o in self.related_ontologywords.all()
            if o.period_enabled), False)

    class Meta:
        ordering = ['-pk']
