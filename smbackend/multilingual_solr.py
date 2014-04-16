# based on http://anthony-tresontani.github.io/Django/2012/09/20/multilingual-search/
from django.conf import settings
from django.utils import translation
from haystack import connections
from haystack.backends.solr_backend import SolrEngine, SolrSearchBackend, SolrSearchQuery
from haystack.constants import DEFAULT_ALIAS

def get_using(language, alias=DEFAULT_ALIAS):
    new_using = alias + "_" + language
    using = new_using if new_using in settings.HAYSTACK_CONNECTIONS else alias
    return using

class MultilingualSolrSearchBackend(SolrSearchBackend):
    def update(self, index, iterable, commit=True, multilingual=True):
        if multilingual:
            initial_language = translation.get_language()[:2]
            # retrieve unique backend name
            backends = []
            for language, __ in settings.LANGUAGES:
                using = get_using(language, alias=self.connection_alias)
                # Ensure each backend is called only once
                if using in backends:
                    continue
                else:
                    backends.append(using)
                translation.activate(language)
                backend = connections[using].get_backend()
                backend.update(index, iterable, commit, multilingual=False)
            translation.activate(initial_language)
        else:
            print("[%s]" % self.connection_alias)
            super(MultilingualSolrSearchBackend, self).update(index, iterable, commit)

class MultilingualSolrSearchQuery(SolrSearchQuery):
    def __init__(self, using=DEFAULT_ALIAS):
        language = translation.get_language()[:2]
        using = get_using(language)
        super(MultilingualSolrSearchQuery, self).__init__(using=using)

class MultilingualSolrEngine(SolrEngine):
    backend = MultilingualSolrSearchBackend
    query = MultilingualSolrSearchQuery
