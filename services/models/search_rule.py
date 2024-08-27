from django.db import models
from django.utils.translation import gettext_lazy as _


class ExclusionRule(models.Model):
    word = models.CharField(max_length=100, verbose_name=_("Word"))
    exclusion = models.CharField(max_length=100, verbose_name=_("Exclusion"))

    class Meta:
        ordering = ["-id"]
        verbose_name = _("Exclusion rule")
        verbose_name_plural = _("Exclusion rules")

    def __str__(self):
        return "%s : %s" % (self.word, self.exclusion)


class ExclusionWord(models.Model):
    word = models.CharField(max_length=100, verbose_name=_("Word"))
    language_short = models.CharField(max_length=2, verbose_name=_("Language short"))

    class Meta:
        ordering = ["-id"]
        verbose_name = _("Exclusion word")
        verbose_name_plural = _("Exclusion words")

    def __str__(self):
        return self.word
