from modeltranslation.translator import TranslationOptions, translator

from eco_counter.models import Station


class StationTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(Station, StationTranslationOptions)
