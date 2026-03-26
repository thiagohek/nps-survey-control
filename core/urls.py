from django.contrib import admin
from django.urls import include, path
from accounts.views import home_redirect

urlpatterns = [
    path('', home_redirect, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('contracts/', include('contracts.urls')),
    path('surveys/', include('surveys.urls')),
    path('schedule/', include('schedule.urls')),
]
