# based on http://anthony-tresontani.github.io/Django/2012/09/20/multilingual-search/
import re
from django.conf import settings
from django.utils import translation
from haystack import connections
from haystack.backends import BaseEngine, BaseSearchBackend, BaseSearchQuery
from haystack.constants import DEFAULT_ALIAS
from haystack.utils.loading import load_backend

class MultilingualSearchBackend(BaseSearchBackend):
    def _operate(self, method_name, *args, **kwargs):
        backends = set()
        for language, _ in settings.LANGUAGES:
            using = '%s-%s' % (self.connection_alias, language)
            # Ensure each backend is called only once
            if using in backends:
                continue
            else:
                backends.add(using)
            with translation.override(language):
                backend = connections[using].get_backend()
                fn = getattr(backend.parent_class, method_name)
                fn(backend, *args, **kwargs)

    def update(self, *args, **kwargs):
        self._operate('update', *args, **kwargs)

    def remove(self, *args, **kwargs):
        self._operate('remove', *args, **kwargs)

    def clear(self, **kwargs):
        return

#class MultilingualSearchQuery(BaseSearchQuery):
#    def __init__(self, using=DEFAULT_ALIAS):

class MultilingualSearchEngine(BaseEngine):
    backend = MultilingualSearchBackend
    #query = MultilingualSearchQuery

    def get_query(self):
        active_language = translation.get_language()
        if not active_language:
            raise ValueError('Please set an active language before doing searches '
                             '(e.g. django.utils.translation.activate("fi"))')
        language = active_language[:2]
        using = '%s-%s' % (self.using, language)
        return connections[using].get_query()

class LanguageSearchBackend(BaseSearchBackend):
    def update(self, *args, **kwargs):
        # Handle all updates through the main Multilingual object.
        return

class LanguageSearchQuery(BaseSearchQuery):
    pass

class LanguageSearchEngine(BaseEngine):
    def __init__(self, **kwargs):
        conn_config = settings.HAYSTACK_CONNECTIONS[kwargs['using']]
        base_engine = load_backend(conn_config['BASE_ENGINE'])(**kwargs)

        backend_bases = (LanguageSearchBackend, base_engine.backend)
        backend_class = type('LanguageSearchBackend', backend_bases,
                             {'parent_class': base_engine.backend})
        self.backend = backend_class

        self.query = base_engine.query

        super(LanguageSearchEngine, self).__init__(**kwargs)
