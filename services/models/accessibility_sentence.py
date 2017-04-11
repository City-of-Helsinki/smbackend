from django.db import models
from .unit import Unit

class AccessibilitySentence(models.Model):
    unit = models.ForeignKey(Unit, db_index=True, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=100)
    group = models.CharField(max_length=100)
    sentence = models.TextField()

    def __str__(self):
        return self.group_name
