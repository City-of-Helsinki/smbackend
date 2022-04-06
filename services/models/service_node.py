from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey

from services.utils import get_translated

from .hierarchy import CustomTreeManager
from .keyword import Keyword
from .service import Service
from .unit import Unit


class ServiceNode(MPTTModel):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey(
        "self", null=True, related_name="children", on_delete=models.CASCADE
    )
    keywords = models.ManyToManyField(Keyword)

    service_reference = models.TextField(null=True)
    related_services = models.ManyToManyField(Service)

    last_modified_time = models.DateTimeField(
        db_index=True, help_text="Time of last modification"
    )

    objects = CustomTreeManager()
    tree_objects = TreeManager()
    search_column_fi = SearchVectorField(null=True)
    search_column_sv = SearchVectorField(null=True)
    search_column_en = SearchVectorField(null=True)

    def __str__(self):
        return "%s (%s)" % (get_translated(self, "name"), self.id)

    def _get_srv_list(self):
        srv_list = set(
            ServiceNode.objects.all().by_ancestor(self).values_list("id", flat=True)
        )
        srv_list.add(self.id)
        return list(srv_list)

    def get_units_qs(self):
        srv_list = self._get_srv_list()
        unit_qs = Unit.objects.filter(
            public=True, is_active=True, service_nodes__in=srv_list
        ).distinct()
        return unit_qs

    def get_unit_count(self):
        srv_list = self._get_srv_list()
        count = (
            Unit.objects.filter(public=True, is_active=True, service_nodes__in=srv_list)
            .distinct()
            .count()
        )
        return count

    @classmethod
    def get_root_service_node(cls, service_node):
        if service_node.parent_id is None:
            return service_node
        else:
            return cls.get_root_service_node(
                ServiceNode.objects.get(id=service_node.parent_id)
            )

    def period_enabled(self):
        """Iterates through related services to find out
        if the tree node has periods enabled via services"""
        return next(
            (o.period_enabled for o in self.related_services.all() if o.period_enabled),
            False,
        )

    class Meta:
        ordering = ["name"]
        indexes = (
            GinIndex(fields=["search_column_fi"]),
            GinIndex(fields=["search_column_sv"]),
            GinIndex(fields=["search_column_en"]),
        )

    @classmethod
    def get_search_column_indexing(cls, lang):
        """
        Defines the columns to be indexed to the search_column
        ,config language and weight.
        """
        if lang == "fi":
            return [
                ("name_fi", "finnish", "A"),
            ]
        elif lang == "sv":
            return [
                ("name_sv", "swedish", "A"),
            ]
        elif lang == "en":
            return [
                ("name_en", "english", "A"),
            ]
        else:
            return []
