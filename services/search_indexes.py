import re

from haystack import indexes, signals
from django.conf import settings
from django.utils.translation import get_language
from django.db import models
from django.apps import apps
from django.db.models import Q
from munigeo.models import AdministrativeDivisionType, Street


class DeleteOnlySignalProcessor(signals.BaseSignalProcessor):
    """
    Delete models from index automatically.

    Use the settings key DISABLE_HAYSTACK_SIGNAL_PROCESSOR to
    disable.
    """
    settings_key = 'DISABLE_HAYSTACK_SIGNAL_PROCESSOR'

    def handle_delete(self, sender, instance, **kwargs):
        if not getattr(settings, self.settings_key, False):
            super().handle_delete(sender, instance, **kwargs)

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
    name = indexes.CharField(model_attr='name', boost=1.125)
    name_sort = indexes.CharField(model_attr='name')
    autosuggest = indexes.EdgeNgramField(model_attr='name')
    autosuggest_exact = indexes.CharField(model_attr='name', boost=1.125)
    extra_searchwords = indexes.CharField()
    autosuggest_extra_searchwords = indexes.CharField()
    public = indexes.BooleanField()
    suggest = indexes.CharField()

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = None

    def get_model(self):
        return self.model

    def get_updated_field(self):
        return 'last_modified_time'

    def prepare_public(self, obj):
        return True

    def _prepare_extra_searchwords(self, obj):
        return ' '.join([category.name for category in obj.keywords.filter(language=get_language())])

    def prepare_extra_searchwords(self, obj):
        return self._prepare_extra_searchwords(obj)

    def prepare_autosuggest_extra_searchwords(self, obj):
        return self._prepare_extra_searchwords(obj)

    def prepare_suggest(self, obj):
        return dict(name=None, service=[], location=[])


class UnitIndex(ServiceMapBaseIndex):
    text = indexes.CharField(document=True, use_template=False)
    name = indexes.CharField(boost=1.125)
    autosuggest = indexes.EdgeNgramField()
    municipality = indexes.CharField(model_attr='municipality_id', null=True)
    services = indexes.MultiValueField()
    root_department = indexes.CharField(null=True)
    suggest = indexes.CharField()
    address = indexes.CharField(use_template=False)

    def read_queryset(self, using=None):
        return self.get_model().search_objects

    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self._street_name_cache = None
        self.model = apps.get_model(app_label='services', model_name='Unit')

    def prepare_public(self, obj):
        return obj.public

    def _get_street_name_cache(self):
        if self._street_name_cache is None:
            self._street_name_cache = set(Street.objects.values_list('name', flat=True))
        return self._street_name_cache

    def _word_matches_street_address(self, word):
        return word in self._get_street_name_cache()

    def _name_with_address_removed(self, name):
        """We remove any street addresses appearing in unit names, because the
        'name', 'text' and 'autosuggest' fields currently decompose
        composite words (yhdyssana) into separate words, which leads
        to confusing false positive matches because street names often
        contain words which have nothing to do with the unit or its
        services (for example "koira" in "koirakalliontie")

        """
        return " ".join((w for w in re.split(r'[ /]+', name)
                         if not self._word_matches_street_address(w)))

    def prepare_name(self, obj):
        return self._name_with_address_removed(obj.name)

    def prepare_autosuggest(self, obj):
        return self._name_with_address_removed(obj.name)

    def prepare_text(self, obj):
        values = [
            self._name_with_address_removed(obj.name),
            obj.service_names(),
            obj.highlight_names()
        ]
        if obj.municipality:
            values.append(obj.municipality.name)
        if obj.department:
            values.append(obj.department.top_departments())
        if obj.address_zip:
            values.append(obj.address_zip)
        return " ".join(values)

    def prepare_services(self, obj):
        return [ow.id for ow in obj.services.all()]

    def prepare_address(self, obj):
        return obj.street_address

    def prepare_root_department(self, obj):
        if obj.root_department is not None:
            return str(obj.root_department.uuid)

    def prepare_suggest(self, obj):
        values = {
            'name': self._name_with_address_removed(obj.name),
            'service': list(set((s.name for s in obj.services.all()))),
            'location': []
        }
        if obj.municipality:
            values['location'].append(obj.municipality.name)
        return values


class ServiceIndex(ServiceMapBaseIndex):
    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = apps.get_model(app_label='services', model_name='Service')


class ServiceNodeIndex(ServiceMapBaseIndex):
    def __init__(self, *args, **kwargs):
        super(*args, **kwargs)
        self.model = apps.get_model(app_label='services', model_name='ServiceNode')

    def index_queryset(self, using=None):
        manager = self.get_model().objects
        # Decision: exclude top level tree nodes (where the level is 0);
        # they are too broad and are not good results for full
        # text queries which are usually trying to be somewhat
        # specific.
        unique_ids = (
            # The query below ensures that duplicate servicenodes
            # are only indexed once. They are servicenodes which
            # have the exact same service reference.
            #
            # Note the empty order_by clause which prevents
            # default ordering from interfering with the grouping.
            manager.exclude(service_reference__isnull=True)
            .values('service_reference')
            .annotate(id=models.Min('id'))
            .values_list('id', flat=True)
            .order_by())

        return manager.filter(
            Q(id__in=unique_ids) | Q(
                # We have to separately add all nodes with null references
                # and level > 0.
                Q(level__gt=0) & Q(service_reference__isnull=True)))


class AddressIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(use_template=False, document=True)
    address = indexes.CharField(use_template=False)
    number = indexes.CharField(use_template=False)
    autosuggest = indexes.EdgeNgramField(use_template=False)
    autosuggest_exact = indexes.CharField(use_template=False)
    public = indexes.BooleanField()

    def prepare_public(self, obj):
        return True

    def get_model(self):
        return apps.get_model('munigeo', 'Address')

    def prepare_text(self, obj):
        return ''

    def prepare_number(self, obj):
        return obj.number

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

    def prepare_autosuggest(self, obj):
        return self.prepare_address(obj)

    def prepare_autosuggest_exact(self, obj):
        return None

    def get_updated_field(self):
        return 'modified_at'


class AdministrativeDivisionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(use_template=False, document=True)
    name = indexes.CharField(use_template=False)
    autosuggest = indexes.EdgeNgramField(use_template=False)
    autosuggest_exact = indexes.CharField(use_template=False)
    public = indexes.BooleanField()

    def prepare_public(self, obj):
        return True

    def get_model(self):
        return apps.get_model('munigeo', 'AdministrativeDivision')

    def prepare_text(self, obj):
        return obj.name

    def prepare_name(self, obj):
        return obj.name

    def prepare_autosuggest(self, obj):
        return self.prepare_name(obj)

    def prepare_autosuggest_exact(self, obj):
        return None

    def get_updated_field(self):
        return 'modified_at'

    def index_queryset(self, using=None):
        manager = self.get_model().objects

        admin_div_types = AdministrativeDivisionType.objects.filter(type__in=('sub_district', 'neighborhood',
                                                                              'postcode_area'))
        manager = manager.filter(type__in=admin_div_types)

        return manager
