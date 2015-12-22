import hashlib
from django.core.cache import cache

def make_cache_key(params, model_name, pk):
    representation_key = _representation_spec_key(params)
    return "sm_{}_{}_{}".format(model_name, representation_key, pk)

def _representation_spec_key(params):
    only = sorted(params.get('only', []))
    include = sorted(params.get('include', []))
    srid = params.get('srid') or []
    key_path = only + include + srid
    key_str = '/'.join(key_path).encode('utf-8')
    return hashlib.md5(key_str).hexdigest()

class SerializerCache(object):
    def _make_key(self, pk):
        #params = self.context.get('request').QUERY_PARAMS
        ret = make_cache_key(self.context, self.cache_model_name, pk)
        return ret
    def cache_get(self, pk):
        return cache.get(self._make_key(pk))
    def cache_set(self, pk, data):
        key = self._make_key(pk)
        return cache.set(key, data)
