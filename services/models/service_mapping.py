from django.db import models

from .ontology_tree_node import OntologyTreeNode

class ServiceMapping(models.Model):
    service_id = models.IntegerField(unique=True)
    node_id = models.ForeignKey(OntologyTreeNode)
    filter = models.TextField(blank=True, null=True, default="")

    def __str__(self):
        if filter:
            return u"map %s -> %s [%s]" % (self.service_id, self.node_id,
                                           self.filter)

        else:
            return u"map %s -> %s" % (self.service_id, self.node_id)
