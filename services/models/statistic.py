from django.db import models
from django.utils.translation import gettext_lazy as _


def default_details():
    return {"embed": 0, "mobile_device": 0}


class RequestStatistic(models.Model):
    timeframe = models.CharField(max_length=10, verbose_name=_("Timeframe"))
    request_counter = models.IntegerField(default=0, verbose_name=_("Request counter"))
    details = models.JSONField(default=default_details, verbose_name=_("Details"))

    class Meta:
        ordering = ["-id"]
        verbose_name = _("Request statistic")
        verbose_name_plural = _("Request statistics")

    def __str__(self):
        return "%s (%s)" % (self.timeframe, self.request_counter)
