from haystack import indexes
from .models import Unit, Service
from django.utils.translation import get_language


class ServiceMapBaseIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    autosuggest = indexes.EdgeNgramField(model_attr='name')
    extra_searchwords = indexes.CharField()
    autosuggest_extra_searchwords = indexes.CharField()

    def get_model(self):
        return None

    def _prepare_extra_searchwords(self, obj):
        return ' '.join([category.name for category in obj.keywords.filter(language=get_language())])

    def prepare_extra_searchwords(self, obj):
        return self._prepare_extra_searchwords(obj)

    def prepare_autosuggest_extra_searchwords(self, obj):
        return self._prepare_extra_searchwords(obj)


class UnitIndex(ServiceMapBaseIndex):

    def get_updated_field(self):
        return 'origin_last_modified_time'

    def get_model(self):
        return Unit


class ServiceIndex(ServiceMapBaseIndex):

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return Service

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(identical_to=None)

    # def prepare(self, obj):
    #     obj.lang_keywords = obj.keywords.filter(language=get_language())
    #     data = super(ServiceIndex, self).prepare(obj)
    #     # if obj.name == 'NAME_TO_BOOST':
    #     #     data['boost'] = 1.1
    #     return data
