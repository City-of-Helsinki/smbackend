from django.contrib.gis.db import models
from django.contrib.postgres.search import SearchVectorField

class SearchView(models.Model):
    # name_fi = models.CharField(max_length=200)
    # name_sv = models.CharField(max_length=200)
    # name_en = models.CharField(max_length=200)    
    type_name = models.CharField(max_length=200)
    vector_column = SearchVectorField()
    class Meta:
        managed = False
        db_table = "search_view"