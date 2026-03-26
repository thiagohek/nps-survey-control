from django.contrib import admin
from .models import ScheduledSurvey


@admin.register(ScheduledSurvey)
class ScheduledSurveyAdmin(admin.ModelAdmin):
    list_display = ('client', 'scheduled_date', 'status', 'last_survey')
    list_filter = ('status', 'scheduled_date', 'client__branch')
    search_fields = ('client__name',)
