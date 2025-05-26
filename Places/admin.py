from django.contrib import admin
from .models import City
from import_export.admin import ImportExportModelAdmin

class CityAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['name', 'id', 'latitude', 'longitude']
    search_fields = ['name']

admin.site.register(City, CityAdmin)