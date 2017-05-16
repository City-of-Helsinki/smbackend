from haystack import indexes, signals
from django.utils.translation import get_language
from django.db import models
from django.apps import apps


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
    autosuggest_exact = indexes.CharField(model_attr='name', boost=1.125)
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
    municipality = indexes.CharField(model_attr='municipality_id', null=True)
    services = indexes.MultiValueField()

    def read_queryset(self, using=None):
        return self.get_model().search_objects

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = apps.get_model(app_label='services', model_name='Unit')

    def get_updated_field(self):
        return 'origin_last_modified_time'

    def prepare_services(self, obj):
        return [service.id for service in obj.services.all()]

class OntologyTreeNodeIndex(ServiceMapBaseIndex):

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = apps.get_model(app_label='services', model_name='OntologyTreeNode')

    def get_updated_field(self):
        return 'last_modified_time'

    def index_queryset(self, using=None):
        manager = self.get_model().objects
        # Decision: exclude top level tree nodes (where the
        # ontologyword reference is null); they are too broad and are
        # not good results for full text queries which are usually
        # trying to be somewhat specific.
        ids = set(
            manager.exclude(ontologyword_reference__isnull=True)
            .values('ontologyword_reference').annotate(id=models.Min('id'))
            .values_list('id', flat=True))
        return manager.filter(id__in=ids)

    # def prepare(self, obj):
    #     obj.lang_keywords = obj.keywords.filter(language=get_language())
    #     data = super(ServiceIndex, self).prepare(obj)
    #     # if obj.name == 'NAME_TO_BOOST':
    #     #     data['boost'] = 1.1
    #     return data


class AddressIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(use_template=False, document=True)
    address = indexes.CharField(use_template=False)

    def get_model(self):
        return apps.get_model('munigeo', 'Address')

    def prepare_text(self, obj):
        return ''

    def prepare_address(self, obj):
        number_end = ""
        letter = ""
        if obj.number_end:
            number_end = "-" + obj.number_end
        if obj.letter:
            letter = obj.letter
        return "{street} {number}{number_end}{letter} {municipality}".format(
            street=obj.street,
            number=obj.number,
            number_end=number_end,
            letter=letter,
            municipality=obj.street.municipality
        )
    def get_updated_field(self):
        return 'modified_at'
