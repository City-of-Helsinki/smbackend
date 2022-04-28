from django.contrib.postgres.indexes import (  # add the Postgres recommended GIN index
    GinIndex,
)
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.fields import ArrayField
from django.db import models

from services.utils import get_translated

from .keyword import Keyword


class Service(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, db_index=True)

    keywords = models.ManyToManyField(Keyword)

    period_enabled = models.BooleanField(default=True)
    clarification_enabled = models.BooleanField(default=True)

    last_modified_time = models.DateTimeField(
        db_index=True, help_text="Time of last modification"
    )
    root_service_node = models.ForeignKey(
        "ServiceNode", null=True, on_delete=models.CASCADE
    )

    search_column_fi = SearchVectorField(null=True)
    search_column_sv = SearchVectorField(null=True)
    search_column_en = SearchVectorField(null=True)

    syllables_fi = ArrayField(models.CharField(max_length=16), default=list)

    def __str__(self):
        return "%s (%s)" % (get_translated(self, "name"), self.id)

    class Meta:
        ordering = ["-pk"]
        indexes = (
            GinIndex(fields=["search_column_fi"]),
            GinIndex(fields=["search_column_sv"]),
            GinIndex(fields=["search_column_en"]),
        )

    @classmethod
    def get_syllable_fi_columns(cls):
        """
        Defines the columns that will be used when populating
        finnish syllables to syllables_fi column. The content 
        will be tokenized to lexems(to_tsvector) and added to 
        the the search_column.
        """
        return [
            "name_fi",     
        ]


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


class UnitServiceDetails(models.Model):
    unit = models.ForeignKey(
        "Unit", db_index=True, related_name="service_details", on_delete=models.CASCADE
    )
    service = models.ForeignKey(
        "Service", db_index=True, related_name="unit_details", on_delete=models.CASCADE
    )
    period_begin_year = models.PositiveSmallIntegerField(null=True)
    period_end_year = models.PositiveSmallIntegerField(null=True)
    clarification = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("period_begin_year", "unit", "service", "clarification_fi")
