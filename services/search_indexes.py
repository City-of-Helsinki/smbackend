from haystack import indexes, signals
from django.utils.translation import get_language
from django.db import models
from django.db.models.loading import get_model

class DeleteOnlySignalProcessor(signals.BaseSignalProcessor):
    """
    Delete models from index automatically.
    """
    def setup(self):
        models.signals.post_delete.connect(self.handle_delete)
        # TODO: ?
        # Efficient would be going through all backends & collecting all models
        # being used, then hooking up signals only for those.

    def teardown(self):
        # Naive (listen to all model saves).
        models.signals.post_delete.disconnect(self.handle_delete)


class ServiceMapBaseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    autosuggest = indexes.EdgeNgramField(model_attr='name')
    extra_searchwords = indexes.CharField()
    autosuggest_extra_searchwords = indexes.CharField()

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = None

    def get_model(self):
        return self.model

    def _prepare_extra_searchwords(self, obj):
        return ' '.join([category.name for category in obj.keywords.filter(language=get_language())])

    def prepare_extra_searchwords(self, obj):
        return self._prepare_extra_searchwords(obj)

    def prepare_autosuggest_extra_searchwords(self, obj):
        return self._prepare_extra_searchwords(obj)


class UnitIndex(ServiceMapBaseIndex):

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = get_model('services', 'Unit')

    def get_updated_field(self):
        return 'origin_last_modified_time'

class ServiceIndex(ServiceMapBaseIndex):

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = get_model('services', 'Service')

    def get_updated_field(self):
        return 'last_modified_time'

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(identical_to=None)

    # def prepare(self, obj):
    #     obj.lang_keywords = obj.keywords.filter(language=get_language())
    #     data = super(ServiceIndex, self).prepare(obj)
    #     # if obj.name == 'NAME_TO_BOOST':
    #     #     data['boost'] = 1.1
    #     return data
