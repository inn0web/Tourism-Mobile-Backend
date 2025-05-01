from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

class ThreadAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    
    list_display = ['thread_id', 'user', 'created_when']
    search_fields = ['thread_id', 'user__username', 'user__email', 'user__first_name', 'user__last_name']
    list_filter = ['created_when']

admin.site.register(Thread, ThreadAdmin)

class ThreadMessageAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['thread', 'is_user_message', 'is_ai_message', 'sent_when']
    list_filter = ['is_ai_message', 'is_user_message', 'sent_when']
    search_fields = ['thread__thread_id', 'thread__user__username', 'thread__user__email', 'thread__user__first_name', 'thread__user__last_name']

admin.site.register(ThreadMessage, ThreadMessageAdmin)