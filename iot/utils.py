from socket import timeout
from django.core.cache import cache
from iot.models import IoTDataSource

CACHE_KEY_PREFIX = __package__
SOURCE_NAMES_KEY = f"{CACHE_KEY_PREFIX}_source_names"
def get_cache_keys(source_name):
    queryset_key = f"{CACHE_KEY_PREFIX}_{source_name}_queryset"
    serializer_key = f"{CACHE_KEY_PREFIX}_{source_name}_serializer"
    return queryset_key, serializer_key

def clear_source_names_from_cache():
    cache.delete(SOURCE_NAMES_KEY)

def get_source_names():
    names = cache.get(SOURCE_NAMES_KEY)
    if not names:
        names = [n for n in IoTDataSource.objects.values_list("source_name", flat=True)]
        cache.set(SOURCE_NAMES_KEY, names, timeout=None)
    return names