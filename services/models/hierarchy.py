from django.db.models import Max, Q, QuerySet
from mptt.models import TreeManager


class CustomTreeManager(TreeManager):
    def get_queryset(self):
        return TreeQuerySet(self.model, using=self._db)

    def determine_max_level(self):
        max_level = self.all().aggregate(max_level=Max("level"))["max_level"]
        if max_level is None:
            # Harrison-Stetson method
            return 10
        return max_level


class TreeQuerySet(QuerySet):
    def by_ancestor(self, ancestor):
        return self.by_ancestors([ancestor])

    def by_ancestors(self, ancestors):
        """Descendants of any of `ancestors`, resolved in a single query."""
        ancestors = list(ancestors)
        if not ancestors:
            return self.none()
        manager = self.model.objects
        max_level = manager.determine_max_level()
        qs = Q()
        # Construct an OR'd queryset for each level of parenthood.
        for i in range(max_level):
            key = "__".join(["parent"] * (i + 1)) + "__in"
            qs |= Q(**{key: ancestors})
        return self.filter(qs)
