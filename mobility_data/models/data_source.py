from django.contrib.gis.db import models

UPLOAD_TO = "data_sources"


class DataSource(models.Model):
    name = models.CharField(max_length=64, default="")
    # Use the type_name as "relation", as foreign key would not
    # work as the ContentTypes are created during import.
    type_name = models.CharField(max_length=3, null=True)
    data_file = models.FileField(upload_to=UPLOAD_TO)
    run_importer = models.BooleanField(default=True)
