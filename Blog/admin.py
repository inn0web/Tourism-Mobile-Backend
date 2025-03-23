from django.contrib import admin
from .models import Blog, BlogImage
from import_export.admin import ImportExportModelAdmin

class BlogAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['title', 'city', 'is_published', 'created_at']

admin.site.register(Blog, BlogAdmin)

class BlogImageAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['blog', 'uploaded_at']
    search_fields = ['blog__title']
    list_filter = ['blog__is_published']

admin.site.register(BlogImage, BlogImageAdmin)