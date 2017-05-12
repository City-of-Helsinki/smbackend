from django.db import models
from django.db.models import QuerySet, Q
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from services.utils import get_translated
from .keyword import Keyword
from .unit import Unit


class OntologyTreeManager(TreeManager):
    def get_queryset(self):
        return OntologyTreeQuerySet(self.model, using=self._db)

    def determine_max_level(self):
        if hasattr(self, '_max_level'):
            return self._max_level
        qs = self.all().order_by('-level')
        if qs.count():
            self._max_level = qs[0].level
        else:
            # Harrison-Stetson method
            self._max_level = 10
        return self._max_level


class OntologyTreeNode(MPTTModel):
    id = models.IntegerField(primary_key=True)  # id of ontologytree
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey('self', null=True, related_name='children')
    unit_count = models.PositiveIntegerField(null=True)
    keywords = models.ManyToManyField(Keyword)

    ontologyword_reference = models.TextField(null=True)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    objects = OntologyTreeManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)

    def get_unit_count(self):
        srv_list = set(OntologyTreeNode.objects.all().by_ancestor(self).values_list('id', flat=True))
        srv_list.add(self.id)
        count = Unit.objects.filter(service_tree_nodes__in=list(srv_list)).distinct().count()
        return count



class OntologyTreeQuerySet(QuerySet):
    def by_ancestor(self, ancestor):
        manager = self.model.objects
        max_level = manager.determine_max_level()
        qs = Q()
        # Construct an OR'd queryset for each level of parenthood.
        for i in range(max_level):
            key = '__'.join(['parent'] * (i + 1))
            qs |= Q(**{key: ancestor})
        return self.filter(qs)
