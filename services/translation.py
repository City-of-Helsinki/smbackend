from modeltranslation.translator import translator, TranslationOptions
from services.models import *

class ServiceTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Service, ServiceTranslationOptions)

class OrganizationTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Organization, OrganizationTranslationOptions)

class DepartmentTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Department, DepartmentTranslationOptions)

class UnitTranslationOptions(TranslationOptions):
    fields = ('name', 'www_url', 'street_address', 'description', 'picture_caption')
translator.register(Unit, UnitTranslationOptions)
