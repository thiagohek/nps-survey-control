from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'branch')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Perfil', {'fields': ('role', 'branch')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Perfil', {'fields': ('role', 'branch')}),
    )
    filter_horizontal = ('branch', 'groups', 'user_permissions')
