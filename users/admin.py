from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'profile_completed', 'is_staff')
    list_filter = ('user_type', 'profile_completed', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'profile_completed')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)