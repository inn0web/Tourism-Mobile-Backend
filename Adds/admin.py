from django.contrib import admin
from .models import Advertisement
from import_export.admin import ImportExportModelAdmin

class AdvertisementAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'button_text', 'button_url', 'start_date', 'end_date', 'is_active', 'priority')
    search_fields = ('title', 'subtitle')
    list_filter = ('is_active', 'start_date', 'end_date')
    ordering = ('-priority',)
    list_editable = ('is_active', 'priority')

admin.site.register(Advertisement, AdvertisementAdmin)