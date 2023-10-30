from modeltranslation.translator import TranslationOptions, translator

from environment_data.models import Station


class StationTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(Station, StationTranslationOptions)
