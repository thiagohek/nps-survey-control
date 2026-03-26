from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('create/', views.SurveyCreateView.as_view(), name='create'),
    path('', views.SurveyListView.as_view(), name='list'),
    path('client/<int:client_id>/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('api/contract/<int:contract_id>/services/', views.ContractServicesApiView.as_view(), name='contract_services_api'),
    path('api/<int:survey_id>/detail/', views.SurveyDetailApiView.as_view(), name='survey_detail_api'),
]
