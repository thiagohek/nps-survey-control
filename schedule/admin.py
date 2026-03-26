from django.contrib import admin
from .models import ScheduledSurvey


@admin.register(ScheduledSurvey)
class ScheduledSurveyAdmin(admin.ModelAdmin):
    list_display = ('get_client_name', 'contract', 'scheduled_date', 'status', 'last_survey')
    list_filter = ('status', 'scheduled_date', 'contract__client__branch')
    search_fields = ('contract__client__name',)

    @admin.display(description='Cliente', ordering='contract__client__name')
    def get_client_name(self, obj):
        return obj.contract.client.name
