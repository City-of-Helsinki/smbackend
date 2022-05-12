from django.contrib.gis.gdal.error import GDALException


def transform_queryset(srid, queryset):
    """
    Transforms all elements in queryset to given srid.
    """
    try:
        for elem in queryset:
            elem.geometry.transform(srid)
    except GDALException:
        return False, queryset
    else:
        return True, queryset
