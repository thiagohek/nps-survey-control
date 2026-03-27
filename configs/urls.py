from django.urls import path
from . import views

app_name = 'configs'

urlpatterns = [
    path('', views.ConfigHomeView.as_view(), name='home'),
    # Usuários
    path('usuarios/', views.UserListView.as_view(), name='user_list'),
    path('usuarios/novo/', views.UserCreateView.as_view(), name='user_create'),
    path('usuarios/<int:pk>/editar/', views.UserUpdateView.as_view(), name='user_update'),
    path('usuarios/<int:pk>/desativar/', views.UserDeactivateView.as_view(), name='user_deactivate'),
    # Pontos Fortes
    path('pontos-fortes/', views.StrengthListView.as_view(), name='strength_list'),
    path('pontos-fortes/novo/', views.StrengthCreateView.as_view(), name='strength_create'),
    path('pontos-fortes/<int:pk>/editar/', views.StrengthUpdateView.as_view(), name='strength_update'),
    # Pontos a Melhorar
    path('pontos-melhorar/', views.ImprovementListView.as_view(), name='improvement_list'),
    path('pontos-melhorar/novo/', views.ImprovementCreateView.as_view(), name='improvement_create'),
    path('pontos-melhorar/<int:pk>/editar/', views.ImprovementUpdateView.as_view(), name='improvement_update'),
    # Serviços
    path('servicos/', views.ServiceListView.as_view(), name='service_list'),
    path('servicos/novo/', views.ServiceCreateView.as_view(), name='service_create'),
    path('servicos/<int:pk>/editar/', views.ServiceUpdateView.as_view(), name='service_update'),
    # Filiais
    path('filiais/', views.FilialListView.as_view(), name='filial_list'),
    path('filiais/novo/', views.FilialCreateView.as_view(), name='filial_create'),
    path('filiais/<int:pk>/editar/', views.FilialUpdateView.as_view(), name='filial_update'),
]
