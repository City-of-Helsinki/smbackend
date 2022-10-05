from django.contrib import admin

from street_maintenance.models import MaintenanceUnit, MaintenanceWork

admin.site.register(MaintenanceWork)
admin.site.register(MaintenanceUnit)
