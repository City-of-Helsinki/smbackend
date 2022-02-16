CACHE_KEY_PREFIX = __package__

def get_cache_keys(source_name):
    queryset_key = f"{CACHE_KEY_PREFIX}_{source_name}_queryset"
    serializer_key = f"{CACHE_KEY_PREFIX}_{source_name}_serializer"
    return queryset_key, serializer_key
