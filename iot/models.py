import json
from xml.parsers.expat import ExpatError

import requests
import xmltodict
from django.core.exceptions import ValidationError
from django.db import models


class IoTDataSource(models.Model):
    source_name = models.CharField(
        max_length=3,
        unique=True,
        verbose_name="Three letter long identifier for the source. "
        "Set the identifier as an argument to the Celery task that fetches the data.",
    )
    source_full_name = models.CharField(max_length=64, null=True)
    is_xml = models.BooleanField(
        default=False, verbose_name="If True, XML data will be converted to JSON."
    )
    url = models.URLField()
    headers = models.JSONField(
        null=True,
        blank=True,
        verbose_name='request headers in JSON format, e.g., {"key1": "value1", "key2": "value2"}',
    )

    def __str__(self):
        return self.source_name

    def clean(self):
        # Test if url exists
        try:
            response = requests.get(self.url, headers=self.headers)
        except requests.exceptions.ConnectionError:
            raise ValidationError(f"The given url {self.url} does not exist.")

        # Test if XML data can be parsed into JSON
        if self.is_xml:
            try:
                xmltodict.parse(response.text)
            except ExpatError as err:
                raise ExpatError(
                    f"Could not parse XML data from the give url {self.url}. {err}"
                )
        else:
            # Test if valid JSON
            try:
                response.json()
            except json.decoder.JSONDecodeError as err:
                raise ValidationError(
                    f"Could not parse the JSON data from the given url {self.url}. {err}"
                )


class IoTData(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    data_source = models.ForeignKey(IoTDataSource, on_delete=models.CASCADE)
    data = models.JSONField(null=True)

    class Meta:
        ordering = ["-created"]
