from django.urls import path
from .views import CEODashboardView

app_name = 'dashboard'

urlpatterns = [
    path('', CEODashboardView.as_view(), name='ceo'),
]
