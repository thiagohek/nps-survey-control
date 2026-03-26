from django.contrib import admin
from .models import Client, ClientService


class ClientServiceInline(admin.TabularInline):
    model = ClientService
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj', 'branch', 'size', 'is_active')
    list_filter = ('size', 'branch', 'is_active')
    search_fields = ('name', 'cnpj', 'contact_name')
    inlines = [ClientServiceInline]
