from modeltranslation.translator import translator, TranslationOptions
from services.models import OntologyWord, UnitOntologyWordDetails, ServiceNode,\
    Department, Unit, UnitConnection, AccessibilitySentence


class OntologyWordTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(OntologyWord, OntologyWordTranslationOptions)


class UnitOntologyWordDetailsTranslationOptions(TranslationOptions):
    fields = ('clarification',)
translator.register(UnitOntologyWordDetails, UnitOntologyWordDetailsTranslationOptions)


class ServiceNodeTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(ServiceNode, ServiceNodeTranslationOptions)


class DepartmentTranslationOptions(TranslationOptions):
    fields = ('name', 'abbr', 'street_address', 'address_city', 'address_postal_full', 'www')
translator.register(Department, DepartmentTranslationOptions)


class UnitTranslationOptions(TranslationOptions):
    fields = ('name', 'www', 'street_address', 'desc', 'short_desc',
              'picture_caption', 'address_postal_full', 'call_charge_info')
translator.register(Unit, UnitTranslationOptions)


class UnitConnectionTranslationOptions(TranslationOptions):
    fields = ('name', 'www')
translator.register(UnitConnection, UnitConnectionTranslationOptions)


class AccessibilitySentenceTranslationOptions(TranslationOptions):
    fields = ('group', 'sentence')
translator.register(AccessibilitySentence, AccessibilitySentenceTranslationOptions)
