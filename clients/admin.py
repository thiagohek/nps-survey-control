from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'branch', 'size', 'is_active')
    list_filter = ('size', 'branch', 'is_active')
    search_fields = ('name', 'cnpj', 'contact_name')
