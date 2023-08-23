from django.db import models
from mptt.managers import TreeManager
from mptt.models import MPTTModel, TreeForeignKey

from services.utils import get_translated

from .hierarchy import CustomTreeManager
from .unit import Unit


class MobilityServiceNode(MPTTModel):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)
    parent = TreeForeignKey(
        "self", null=True, related_name="children", on_delete=models.CASCADE
    )
    service_reference = models.TextField(null=True)
    last_modified_time = models.DateTimeField(
        db_index=True, help_text="Time of last modification"
    )
    objects = CustomTreeManager()
    tree_objects = TreeManager()

    def __str__(self):
        return "%s (%s)" % (get_translated(self, "name"), self.id)

    def _get_srv_list(self):
        srv_list = set(
            MobilityServiceNode.objects.all()
            .by_ancestor(self)
            .values_list("id", flat=True)
        )
        srv_list.add(self.id)
        return list(srv_list)

    def get_units_qs(self):
        srv_list = self._get_srv_list()
        unit_qs = Unit.objects.filter(
            public=True, is_active=True, mobility_service_nodes__in=srv_list
        ).distinct()
        return unit_qs

    def get_unit_count(self):
        srv_list = self._get_srv_list()
        count = (
            Unit.objects.filter(
                public=True, is_active=True, mobility_service_nodes__in=srv_list
            )
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
                MobilityServiceNode.objects.get(id=service_node.parent_id)
            )

    class Meta:
        ordering = ["name"]
