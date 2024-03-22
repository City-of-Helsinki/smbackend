from modeltranslation.translator import TranslationOptions, translator

from exceptional_situations.models import SituationAnnouncement


class SituationAnnouncementTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "description",
    )


translator.register(SituationAnnouncement, SituationAnnouncementTranslationOptions)
