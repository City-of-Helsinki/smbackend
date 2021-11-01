from django.contrib.gis.gdal.error import GDALException

def transform_queryset(srid, queryset):
    try:
        for elem in queryset:
            elem.geometry.transform(srid)
    except GDALException:
        return False, queryset
    else:   
        return True, queryset

def transform_group_queryset(srid, queryset):
    try: 
        for unit in queryset:
            unit.geometry.transform(srid)

    except GDALException:
        return False, queryset
    else:    
        return True, queryset
    
