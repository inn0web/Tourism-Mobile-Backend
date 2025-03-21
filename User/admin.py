from django.contrib import admin
from .models import User, PasswordResetCode

class UserAdmin(admin.ModelAdmin):

    list_display = ['email', 'first_name', 'last_name', 'phone', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone', 'username']

admin.site.register(User, UserAdmin)

class PasswordResetCodeAdmin(admin.ModelAdmin):

    list_display = ['user', 'code', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'code']

admin.site.register(PasswordResetCode, PasswordResetCodeAdmin)