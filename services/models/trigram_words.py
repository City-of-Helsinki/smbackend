from django.contrib.gis.db import models

class TrigramWords(models.Model):
  
    name_fi = models.CharField(max_length=255)
    name_sv = models.CharField(max_length=255)
    
    class Meta:
        managed = False
        db_table = "trigram_words"