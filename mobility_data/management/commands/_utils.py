from django.conf import settings
from django.contrib.gis.gdal import DataSource

from mobility_data.models import ContentType


def get_test_gdal_data_source(file_name):
    """
    Returns the given file_name as a GDAL Datasource,
    the file must be located in /mobility_data/tests/data/
    """
    path = f"{settings.BASE_DIR}/{ContentType._meta.app_label}/tests/data/"
    return DataSource(path + file_name)
