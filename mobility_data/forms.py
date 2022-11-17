from django import forms
from django.forms import ChoiceField

from mobility_data.constants import DATA_SOURCE_IMPORTERS
from mobility_data.models import DataSource


class CustomDataSourceForm(forms.ModelForm):
    type_names = [(key, key) for key in DATA_SOURCE_IMPORTERS.keys()]
    type_name = ChoiceField(choices=tuple(type_names))

    class Meta:
        fields = "__all__"
        model = DataSource
