from modeltranslation.translator import translator, register, TranslationOptions
from services.models import *


class OntologyWordTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(OntologyWord, OntologyWordTranslationOptions)


class OntologyTreeNodeTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(OntologyTreeNode, OntologyTreeNodeTranslationOptions)


class OrganizationTranslationOptions(TranslationOptions):
    fields = ('name', 'abbr', 'street_address', 'address_city', 'address_postal_full', 'www')
translator.register(Organization, OrganizationTranslationOptions)


class DepartmentTranslationOptions(TranslationOptions):
    fields = ('name', 'abbr', 'street_address', 'address_city', 'address_postal_full', 'www')
translator.register(Department, DepartmentTranslationOptions)


class UnitTranslationOptions(TranslationOptions):
    fields = ('name', 'www', 'street_address', 'desc', 'short_desc', 'picture_caption', 'address_postal_full')
translator.register(Unit, UnitTranslationOptions)


class UnitConnectionTranslationOptions(TranslationOptions):
    fields = ('name', 'www')
translator.register(UnitConnection, UnitConnectionTranslationOptions)


class AccessibilitySentenceTranslationOptions(TranslationOptions):
    fields = ('group', 'sentence')
translator.register(AccessibilitySentence, AccessibilitySentenceTranslationOptions)
