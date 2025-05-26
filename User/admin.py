from django.contrib import admin
from .models import User, PasswordResetCode, Category, UserSavedPlace, UserSearchHistory
from import_export.admin import ImportExportModelAdmin

class UserAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['email', 'first_name', 'last_name', 'phone', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone', 'username']

admin.site.register(User, UserAdmin)

class PasswordResetCodeAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['user', 'code', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'code']

admin.site.register(PasswordResetCode, PasswordResetCodeAdmin)

class CategoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['name', 'id', 'icon']
    search_fields = ['name', 'id']

admin.site.register(Category, CategoryAdmin)

class UserSavedPlacesAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['user', 'place_id', 'city_name', 'date']
    search_fields = ['user__email', 'place_id', 'city_name']
    list_filter = ['date']

admin.site.register(UserSavedPlace, UserSavedPlacesAdmin)

class UserSearchHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['search', 'user', 'date']
    list_filter = ['date']

admin.site.register(UserSearchHistory, UserSearchHistoryAdmin)