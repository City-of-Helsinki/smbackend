from modeltranslation.translator import TranslationOptions, translator

from services.models import (
    Announcement,
    Department,
    ErrorMessage,
    Service,
    ServiceNode,
    Unit,
    UnitConnection,
    UnitEntrance,
    UnitServiceDetails,
)


class ServiceTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(Service, ServiceTranslationOptions)


class UnitServiceDetailsTranslationOptions(TranslationOptions):
    fields = ("clarification",)


translator.register(UnitServiceDetails, UnitServiceDetailsTranslationOptions)


class ServiceNodeTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(ServiceNode, ServiceNodeTranslationOptions)


class DepartmentTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "abbr",
        "street_address",
        "address_city",
        "address_postal_full",
        "www",
    )


translator.register(Department, DepartmentTranslationOptions)


class UnitTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "www",
        "street_address",
        "description",
        "short_description",
        "picture_caption",
        "address_postal_full",
        "call_charge_info",
    )


translator.register(Unit, UnitTranslationOptions)


class UnitConnectionTranslationOptions(TranslationOptions):
    fields = ("name", "www")


translator.register(UnitConnection, UnitConnectionTranslationOptions)


class NotificationTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "lead_paragraph",
        "content",
        "external_url",
        "external_url_title",
    )


translator.register(Announcement, NotificationTranslationOptions)
translator.register(ErrorMessage, NotificationTranslationOptions)


class UnitEntranceTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(UnitEntrance, UnitEntranceTranslationOptions)
