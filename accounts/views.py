from django.contrib.auth import views as auth_views
from django.shortcuts import redirect


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'


class LogoutView(auth_views.LogoutView):
    pass


def home_redirect(request):
    """Redireciona para a página adequada baseado no role do usuário."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if request.user.is_manager():
        return redirect('clients:list')
    return redirect('clients:list')
