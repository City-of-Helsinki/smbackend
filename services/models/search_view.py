from django.contrib.gis.db import models
from django.contrib.postgres.search import SearchVectorField


class SearchView(models.Model):
    type_name = models.CharField(max_length=200)
    search_column = SearchVectorField()

    class Meta:
        managed = False
        db_table = "search_view"
