from django.contrib import admin
from .models import Filial, Service


@admin.register(Filial)
class FilialAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
