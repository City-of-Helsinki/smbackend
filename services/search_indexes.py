from haystack import indexes
from .models import Unit, Service
from django.utils.translation import get_language


class UnitIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    autosuggest = indexes.EdgeNgramField(model_attr='name')

    def get_updated_field(self):
        return 'origin_last_modified_time'

    def get_model(self):
        return Unit

    def prepare(self, obj):
        obj.lang_keywords = obj.keywords.filter(language=get_language())
        return super(UnitIndex, self).prepare(obj)


class ServiceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name', use_template=False)
    autosuggest = indexes.EdgeNgramField(model_attr='name')

    def get_updated_field(self):
        return 'last_modified_time'

    def get_model(self):
        return Service

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(identical_to=None)
