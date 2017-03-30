from django.db import models
from django.db.models import QuerySet
from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from services.utils import get_translated
from .keyword import Keyword


# ex. ServiceType
class Service(models.Model):
    id = models.IntegerField(primary_key=True)  # id of ontologyword
    name = models.CharField(max_length=200, db_index=True)

    unit_count = models.PositiveIntegerField(null=True)
    keywords = models.ManyToManyField(Keyword)

    last_modified_time = models.DateTimeField(db_index=True, help_text='Time of last modification')

    def __str__(self):
        return "%s (%s)" % (get_translated(self, 'name'), self.id)


class ServiceManager(TreeManager):
    def get_queryset(self):
        return ServiceQuerySet(self.model, using=self._db)

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


class ServiceQuerySet(QuerySet):
    def by_ancestor(self, ancestor):
        manager = self.model.objects
        max_level = manager.determine_max_level()
        qs = Q()
        # Construct an OR'd queryset for each level of parenthood.
        for i in range(max_level):
            key = '__'.join(['parent'] * (i + 1))
            qs |= Q(**{key: ancestor})
        return self.filter(qs)
