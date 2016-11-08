from modeltranslation.translator import translator, TranslationOptions
from observations.models import AllowedValue

class AllowedValueTranslationOptions(TranslationOptions):
    fields = ('name','description')
translator.register(AllowedValue, AllowedValueTranslationOptions)
