from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='list'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='update'),
    path('import/', views.ClientImportView.as_view(), name='import'),
]
