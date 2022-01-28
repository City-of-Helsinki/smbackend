from django.contrib import admin

from .models import (
    AllowedValue,
    CategoricalObservation,
    DescriptiveObservation,
    ObservableProperty,
    PluralityAuthToken,
)

admin.site.register(PluralityAuthToken, admin.ModelAdmin)
admin.site.register(ObservableProperty, admin.ModelAdmin)
admin.site.register(AllowedValue, admin.ModelAdmin)
admin.site.register(CategoricalObservation, admin.ModelAdmin)
admin.site.register(DescriptiveObservation, admin.ModelAdmin)
