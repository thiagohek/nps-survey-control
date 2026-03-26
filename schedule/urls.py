from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    path('', views.CalendarView.as_view(), name='calendar'),
    path('api/events/', views.CalendarEventsApiView.as_view(), name='events_api'),
]
