from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from services.models.notification import Announcement, ErrorMessage
from services.models.search_rule import ExclusionWord


class NotificationAdmin(TranslationAdmin):
    list_display = ("title", "active", "content")
    list_display_links = ("title", "content")
    list_filter = ("active",)


class ExlusionWordForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super().clean()
        accepted_language_shorts = [lang[0] for lang in settings.LANGUAGES]
        if cleaned_data.get("language_short") not in accepted_language_shorts:
            raise ValidationError(
                _("Language short must be one of")
                + f":{' ,'.join(accepted_language_shorts)}"
            )
        return cleaned_data


class ExclusionWordAdmin(admin.ModelAdmin):
    list_display = ("word", "language_short")

    model = ExclusionWord
    form = ExlusionWordForm


admin.site.register(ExclusionWord, ExclusionWordAdmin)
admin.site.register(Announcement, NotificationAdmin)
admin.site.register(ErrorMessage, NotificationAdmin)
