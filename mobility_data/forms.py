from django import forms
from django.forms import ChoiceField

from mobility_data.constants import DATA_SOURCE_IMPORTERS
from mobility_data.models import DataSource


class CustomDataSourceForm(forms.ModelForm):
    # Instead of the type name, display the more informative importer or the optional display name to the user.
    type_names = [
        (key, value["display_name"])
        if "display_name" in value
        else (key, value["importer_name"])
        for key, value in DATA_SOURCE_IMPORTERS.items()
    ]

    type_name = ChoiceField(choices=tuple(type_names))

    class Meta:
        fields = "__all__"
        model = DataSource
