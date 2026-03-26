from django.contrib import admin
from .models import Contract, ContractService


class ContractServiceInline(admin.TabularInline):
    model = ContractService
    extra = 0
    readonly_fields = ('service',)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('client', 'start_date', 'end_date', 'status', 'company_size', 'survey_frequency_days')
    list_filter = ('status', 'company_size', 'client__branch')
    search_fields = ('client__name', 'client__cnpj')
    raw_id_fields = ('client',)
    readonly_fields = ('company_size', 'survey_frequency_days', 'last_survey_date', 'created_at')
    inlines = [ContractServiceInline]
