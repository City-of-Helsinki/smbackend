from modeltranslation.translator import TranslationOptions, translator

from observations.models import AllowedValue, ObservableProperty


class AllowedValueTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


translator.register(AllowedValue, AllowedValueTranslationOptions)


class ObservablePropertyTranslationOptions(TranslationOptions):
    fields = ('name',)


translator.register(ObservableProperty, ObservablePropertyTranslationOptions)
