from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    path('create/', views.ContractCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ContractDetailView.as_view(), name='detail'),
    path('<int:pk>/close/', views.ContractCloseView.as_view(), name='close'),
    path('api/<int:contract_id>/services/', views.ContractServicesApiView.as_view(), name='services_api'),
]
