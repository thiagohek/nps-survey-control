from django.contrib import admin
from .models import Survey, ServiceScore, Strength, Improvement


class ServiceScoreInline(admin.TabularInline):
    model = ServiceScore
    extra = 1


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('get_client_name', 'contract', 'date_conducted', 'nps_score', 'respondent_name', 'is_historical', 'created_by')
    list_filter = ('is_historical', 'date_conducted', 'contract__client__branch')
    search_fields = ('contract__client__name', 'respondent_name')
    date_hierarchy = 'date_conducted'
    inlines = [ServiceScoreInline]
    filter_horizontal = ('strengths', 'improvements')

    @admin.display(description='Cliente', ordering='contract__client__name')
    def get_client_name(self, obj):
        return obj.contract.client.name


@admin.register(Strength)
class StrengthAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Improvement)
class ImprovementAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
