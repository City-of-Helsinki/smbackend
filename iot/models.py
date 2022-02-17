import requests
import json
from django.db import models
from django.core.exceptions import ValidationError


class IoTDataSource(models.Model):
    source_name = models.CharField(
        max_length=3, unique=True, verbose_name="Three letter long name for the source"
    )
    source_full_name = models.CharField(max_length=64, null=True)
    url = models.URLField()

    def __str__(self):
        return self.source_name

    def clean(self):
        # Test if url exists
        try:
            response = requests.get(self.url)
        except requests.exceptions.ConnectionError:
            raise ValidationError(f"The given url {self.url} does not exist.")
        # Test if valid json
        try:
            json_data = response.json()
        except json.decoder.JSONDecodeError:
            raise ValidationError(
                f"Could not parse the JSON data for the given url {self.url}"
            )


class IoTData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    data_source = models.ForeignKey(IoTDataSource, on_delete=models.CASCADE)
    data = models.JSONField(null=True)
