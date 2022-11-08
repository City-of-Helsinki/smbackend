from django.db import models
from django.utils.translation import gettext_lazy as _

from services.models.department import Department

DEFAULT_SERVICE_CODE = "2809"


class FeedbackMapping(models.Model):
    abbr_fi = models.CharField(max_length=10, verbose_name=_("Abbreviation (fi)"))
    service_code = models.CharField(
        max_length=10, default=DEFAULT_SERVICE_CODE, verbose_name=_("Service code")
    )
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    organization = models.ForeignKey(
        Department,
        related_name="organization_feedback_mappings",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = _("Feedback mapping")
        verbose_name_plural = _("Feedback mappings")
        unique_together = (("service_code", "department"),)

    def __str__(self):
        return "%s (%s)" % (self.abbr_fi, self.service_code)
