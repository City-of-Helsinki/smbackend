from haystack import indexes
from .models import Unit, Service


class UnitIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name', use_template=False)
    autosuggest = indexes.EdgeNgramField(model_attr='name')

    def get_updated_field(self):
        return 'origin_last_modified_time'

    def get_model(self):
        return Unit


class ServiceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name', use_template=False)
    autosuggest = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return Service
