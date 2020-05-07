from django.db import models

from .service_node import ServiceNode


class ServiceMapping(models.Model):
    service_id = models.IntegerField(unique=True)
    node_id = models.ForeignKey(ServiceNode, on_delete=models.CASCADE)
    filter = models.TextField(blank=True, null=True, default="")

    def __str__(self):
        if filter:
            return u"map %s -> %s [%s]" % (self.service_id, self.node_id,
                                           self.filter)

        else:
            return u"map %s -> %s" % (self.service_id, self.node_id)
