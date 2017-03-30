from modeltranslation.translator import translator, register, TranslationOptions
from services.models import *


class ServiceTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Service, ServiceTranslationOptions)


class OrganizationTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Organization, OrganizationTranslationOptions)


class DepartmentTranslationOptions(TranslationOptions):
    fields = ('name', 'abbr', 'street_address', 'address_city', 'address_postal_full', 'www')
translator.register(Department, DepartmentTranslationOptions)


class UnitTranslationOptions(TranslationOptions):
    fields = ('name', 'www_url', 'street_address', 'description', 'picture_caption')
translator.register(Unit, UnitTranslationOptions)


class UnitConnectionTranslationOptions(TranslationOptions):
    fields = ('name', 'www_url')
translator.register(UnitConnection, UnitConnectionTranslationOptions)


class ServiceTreeNodeTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(ServiceTreeNode, ServiceTreeNodeTranslationOptions)